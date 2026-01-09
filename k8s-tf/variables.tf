variable "name" {
  description = "The name to use for all resources created by this module"
  type        = string
  default     = "tta-graph-kube"
}

variable "image" {
  description = "The Docker image to run"
  type        = string
  default     = "mcarroll321/"
}

variable "container_port" {
  description = "The port the Docker image listens on"
  type        = number
  default     = 8000
}

variable "replicas" {
  description = "How many replicas to run"
  type        = number
  default     = 1
}