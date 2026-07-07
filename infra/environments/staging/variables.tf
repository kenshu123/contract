# このファイルはstaging環境全体で使う入力変数を定義する

# AWSリソースを作成するリージョン
variable "aws_region" {
  description = "AWSリソースを作成するリージョン"
  type        = string
  default     = "ap-northeast-1"
}

# VPC全体に割り当てるCIDRブロック
variable "vpc_cidr" {
  description = "staging VPC の CIDR ブロック"
  type        = string
  default     = "10.0.0.0/16"
}

# AZ1に配置するパブリックサブネットのCIDR
variable "public_subnet_cidr_az1" {
  description = "AZ1 パブリックサブネットの CIDR ブロック"
  type        = string
  default     = "10.0.1.0/24"
}

# AZ2に配置するパブリックサブネットのCIDR
variable "public_subnet_cidr_az2" {
  description = "AZ2 パブリックサブネットの CIDR ブロック"
  type        = string
  default     = "10.0.2.0/24"
}

# AZ1に配置するプライベートサブネットのCIDR
variable "private_subnet_cidr_az1" {
  description = "AZ1 プライベートサブネットの CIDR ブロック"
  type        = string
  default     = "10.0.11.0/24"
}

# AZ2に配置するプライベートサブネットのCIDR
variable "private_subnet_cidr_az2" {
  description = "AZ2 プライベートサブネットの CIDR ブロック"
  type        = string
  default     = "10.0.12.0/24"
}

# 1つ目のサブネットを配置するアベイラビリティゾーン
variable "az1" {
  description = "1つ目のパブリックサブネットを配置する AZ"
  type        = string
  default     = "ap-northeast-1a"
}

# 2つ目のサブネットを配置するアベイラビリティゾーン
variable "az2" {
  description = "2つ目のパブリックサブネットを配置する AZ"
  type        = string
  default     = "ap-northeast-1c"
}

# Anthropic APIキー（アプリ起動に必須）
variable "anthropic_api_key" {
  description = "Anthropic API キー"
  type        = string
  sensitive   = true
}

# アプリの API キー（リクエスト認証に使用）
variable "api_key" {
  description = "アプリの API キー（Authorization: Bearer に指定する値）"
  type        = string
  sensitive   = true
}
