# このファイルはstaging環境のプロバイダー設定とモジュール呼び出しを定義する

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# stagingリージョンを ap-northeast-1 に作成するプロバイダー設定
provider "aws" {
  region = var.aws_region
}

# VPC・パブリックサブネット・IGW・ルートテーブルを作成するnetworkモジュール
module "network" {
  source = "../../modules/network"

  vpc_cidr               = var.vpc_cidr
  public_subnet_cidr_az1 = var.public_subnet_cidr_az1
  public_subnet_cidr_az2 = var.public_subnet_cidr_az2
  az1                     = var.az1
  az2                     = var.az2
  private_subnet_cidr_az1 = var.private_subnet_cidr_az1
  private_subnet_cidr_az2 = var.private_subnet_cidr_az2
  project_name            = "contract-checker-staging"
}

# コンテナイメージを保存するECRリポジトリを作成するecrモジュール
module "ecr" {
  source = "../../modules/ecr"

  repository_name = "contract-checker-shirayamahiroto"
}

# ---------------------------------------------------------------
# ECS タスク用セキュリティグループ（循環依存を避けるため staging で直接定義）
#
# rds モジュールは「ECS タスク SG の ID」を受け取り ingress ルールに使う。
# ecs_service モジュールは「ECS タスク SG」を使ってタスクを起動する。
# 両モジュールが互いを参照すると循環依存になるため、SG をここで先に作り
# 両モジュールに渡す構成にしている。
# ---------------------------------------------------------------
resource "aws_security_group" "ecs_task" {
  name        = "contract-checker-staging-ecs-task-sg"
  description = "ECS task: allow inbound on container port from ALB only"
  vpc_id      = module.network.vpc_id

  # アウトバウンドは全許可（ECR イメージ Pull・Secrets Manager・外部 API 呼び出し用）
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "contract-checker-staging-ecs-task-sg2"
  }
}

# PostgreSQL RDS インスタンスを作成する rds モジュール
# プライベートサブネットに配置し、ECS タスク SG からのみ接続を許可する
module "rds" {
  source = "../../modules/rds"

  identifier        = "contract-checker-staging"
  db_name           = "contractchecker"
  db_username       = "dbadmin"
  instance_class    = "db.t3.micro"
  allocated_storage = 20

  vpc_id                     = module.network.vpc_id
  subnet_ids                 = module.network.public_subnet_ids  # 既存インスタンスの配置に合わせる（移行はスナップショット再作成が必要）
  ecs_task_security_group_id = aws_security_group.ecs_task.id
}

# Secrets Manager 読み取りと CloudWatch Logs 書き込みに絞った最小権限タスクロール
module "iam" {
  source = "../../modules/iam"

  project_name             = "contract-checker-staging"
  rds_secret_arn           = module.rds.master_secret_arn
  cloudwatch_log_group_arn = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/contract-checker-staging"
}

# 現在の AWS アカウント ID をロググループ ARN の組み立てに使う
data "aws_caller_identity" "current" {}

# ECSクラスター・タスク定義・サービスを作成するecs_serviceモジュール
module "ecs_service" {
  source = "../../modules/ecs_service"

  project_name               = "contract-checker-staging"
  vpc_id                     = module.network.vpc_id
  subnet_ids                 = module.network.private_subnet_ids
  alb_subnet_ids             = module.network.public_subnet_ids
  container_image            = "${module.ecr.repository_url}:latest"
  health_check_path          = "/health"
  ecs_task_security_group_id = aws_security_group.ecs_task.id
  task_role_arn              = module.iam.ecs_task_role_arn  # 最小権限タスクロールを紐づける

  container_environment = {
    ANTHROPIC_API_KEY = var.anthropic_api_key
    API_KEY           = var.api_key
    DB_SECRET_ARN     = module.rds.master_secret_arn
    DB_HOST           = module.rds.db_host
    DB_PORT           = tostring(module.rds.db_port)
    DB_NAME           = module.rds.db_name
  }

  depends_on = [module.rds]
}
