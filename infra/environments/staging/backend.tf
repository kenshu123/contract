terraform {
  backend "s3" {
    # infra/bootstrap で作成した共有バケット
    bucket = "contract-checker-uploads-shirayamahiroto"

    # 環境ごとに key を分けることで、1 つのバケットで複数の state を管理できる
    key = "staging/terraform.tfstate"

    region = "ap-northeast-1"

    encrypt = true

    # --- なぜロック（state locking）が必要か ---
    # 複数の terraform apply が同時に走ると、それぞれが同じ state を読み込んだ後に
    # 別々の変更を書き込む。後から書いた apply が先の apply の変更を丸ごと上書きし、
    # インフラの実態と state が乖離する「lost update」が発生する。
    # ロックはこれを防ぐ排他制御で、apply 開始時に取得し、完了時に解放する。
    #
    # Terraform S3 backend の標準的なロック実装は DynamoDB だが、
    # 本プロジェクトでは DynamoDB を使用しない。
    # そのため、CI ワークフロー側で同時実行を抑制する
    # （GitHub Actions の concurrency グループ設定など）ことで代替する。
  }
}
