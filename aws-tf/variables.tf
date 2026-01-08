variable "name" {
  description = "The name to use for the EKS cluster"
  type        = string
  default     = "TTA-Notif"
}

variable "min_size" {
  description = "Minimum number of nodes to have in the EKS cluster"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of nodes to have in the EKS cluster"
  type        = number
  default     = 2
}

variable "desired_size" {
  description = "Desired number of nodes to have in the EKS cluster"
  type        = number
  default     = 2
}

variable "instance_types" {
  description = "The types of EC2 instances to run in the node group"
  type        = list(string)
  default     = ["t3.small"]
}