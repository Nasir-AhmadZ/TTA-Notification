terraform {
  required_version = ">= 1.0.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.20.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.38.0"
    }
  }
}

data "terraform_remote_state" "eks" {
  backend = "local"

  config = {
    path = "../aws-tf/terraform.tfstate"
  }
}

data "aws_eks_cluster" "cluster" {
  name = data.terraform_remote_state.eks.outputs.cluster_name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority.0.data)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      data.aws_eks_cluster.cluster.name
    ]
  }
}

resource "kubernetes_deployment" "nginx" {
  metadata {
    name = "ttanotifapp"
    labels = {
      App = "TTA-Notif-app"
    }
  }

  spec {
    replicas = var.replicas
    selector {
      match_labels = {
        App = "TTA-Notif-app"
      }
    }
    template {
      metadata {
        labels = {
          App = "TTA-Notif-app"
        }
      }
      spec {
        container {
          image = "mcarroll321/tta-notif"
          name  = "ttanotifcontainer"

          port {
            container_port = 8003
          }

          env {
            name = "RABBIT_URL"
            value = "amqps://dawzqycu:Gbcocn8dbUVYY8sFLjVVkFu3ZIVfkC2B@hawk.rmq.cloudamqp.com/dawzqycu"
          }
          env {
            name = "MONGO_URI"
            value = "mongodb+srv://User:Password@cluster0.82ogu5x.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
          }

          resources {
            limits = {
              cpu    = "0.5"
              memory = "512Mi"
            }
            requests = {
              cpu    = "250m"
              memory = "50Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "nginx" {
  metadata {
    name = "ttanotifservice"
  }
  spec {
    selector = {
      App = kubernetes_deployment.nginx.spec.0.template.0.metadata[0].labels.App
    }
    port {
      port        = 8003
      target_port = 8003
    }

    type = "LoadBalancer"
  }
}