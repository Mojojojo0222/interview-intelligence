resource "aws_ecr_repository" "interview_service" {
  name                 = "interview-service"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "interview-frontend"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_lifecycle_policy" "cleanup" {
  for_each   = toset([aws_ecr_repository.interview_service.name, aws_ecr_repository.frontend.name])
  repository = each.value
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_s3_bucket" "reports" {
  bucket = "${var.project}-reports-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id
  versioning_configuration { status = "Enabled" }
}

data "aws_caller_identity" "current" {}

output "ecr_interview_service_url" { value = aws_ecr_repository.interview_service.repository_url }
output "ecr_frontend_url"          { value = aws_ecr_repository.frontend.repository_url }
output "s3_reports_bucket"         { value = aws_s3_bucket.reports.bucket }
