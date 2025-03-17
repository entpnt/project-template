// Define variables with defaults
variable "PROJECT_NAME" {
  default = "project-flow"
}

variable "FLASK_ENV" {
  default = "development"
}

// Common group for shared configuration
group "default" {
  targets = ["api-development"]
}

// Development target
target "api-development" {
  context = "."
  dockerfile = "Dockerfile"
  tags = ["${PROJECT_NAME}-api:dev"]
  args = {
    FLASK_ENV = "development"
  }
}

// Production target
target "api-production" {
  context = "."
  dockerfile = "Dockerfile"
  tags = ["${PROJECT_NAME}-api:prod"]
  args = {
    FLASK_ENV = "production"
  }
}

// Testing target
target "api-testing" {
  context = "."
  dockerfile = "Dockerfile.test"
  tags = ["${PROJECT_NAME}-api:test"]
  args = {
    FLASK_ENV = "testing"
  }
} 