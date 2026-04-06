# CDK Project Template

This project is an advanced AWS Cloud Development Kit (CDK) template designed for enterprise-grade scalability, clean separation of concerns, and multi-environment deployments. It uses a structured three-stack architecture to organize resources effectively.

## Architecture Overview

The infrastructure is broken down into three distinct stacks per environment to reduce blast radius and manage state safely.

### 1. Stateful Stack (`lib/stateful`)
The **Stateful Stack** is responsible for resources that hold persistent data. These resources are typically the hardest to recreate and should have strict deletion policies.
- **Examples**: Amazon DynamoDB, Amazon RDS, Amazon S3 (Data/Assets), Amazon Cognito User Pools.
- **Why separate?**: Changes to stateless resources (like a Lambda function) should never accidentally impact or delete stateful resources. You deploy this stack less frequently.

### 2. Stateless Stack (`lib/stateless`)
The **Stateless Stack** holds ephemeral resources or resources that can be easily recreated from source code without data loss.
- **Examples**: AWS Lambda functions, Amazon API Gateway, AWS AppSync, ECS Tasks.
- **How it connects**: The Stateless Stack receives references (like table ARNs or bucket names) from the Stateful Stack via stack props. This prevents hardcoding ARNs and ensures tight coupling where needed.

### 3. Global Stack (`lib/global`)
The **Global Stack** is used for resources that span multiple regions or are tied to edge locations. This stack is typically deployed to `us-east-1` regardless of where the rest of your infrastructure lives.
- **Examples**: Amazon CloudFront distributions, AWS WAF (Web Application Firewall) attached to CloudFront, ACM (AWS Certificate Manager) certificates for CloudFront.
- **How it connects**: The Global stack usually needs the API Gateway endpoint or S3 Website Bucket (from the Stateless or Stateful stacks) to set up CloudFront origins.

---

## Directory Structure

```text
├── bin/
│   ├── cdk-template-bren.ts     # Main entry point for the CDK application
│   └── environments/            # Logic to stitch the 3 stacks together per env
│       ├── base.ts              # Core logic to wire Stateful -> Stateless -> Global
│       ├── dev.ts               # Setup dev environment
│       ├── staging.ts           # Setup staging environment
│       └── prod.ts              # Setup production environment
├── configs/                     # Environment-specific configuration values
│   ├── dev.ts                   # e.g. "template-dev", open CORS origins
│   ├── staging.ts               # e.g. "template-staging"
│   └── prod.ts                  # e.g. "template-prod", strict CORS origins
├── lib/
│   ├── global/                  # Global Stack definition
│   │   └── constructs/          # Global constructs (e.g., CloudFront, WAF)
│   ├── stateful/                # Stateful Stack definition
│   │   └── constructs/          # Stateful constructs (e.g., S3, DynamoDB, Cognito)
│   ├── stateless/               # Stateless Stack definition
│   │   └── constructs/          # Stateless constructs (e.g., Lambda, API Gateway)
│   └── types/                   # Shared TypeScript interfaces (e.g., StackProps)
```

---

## Constructs and Resources

Within each stack directory (`lib/global`, `lib/stateful`, `lib/stateless`), you will find a `constructs/` subdirectory. This is where you define your reusable AWS resource groupings (L3 constructs).

- **Purpose**: Instead of declaring all AWS resources directly within the stack file, you create modular, purpose-built `Construct` classes. Each `Construct` encapsulates a set of related AWS resources and their configurations.
- **Benefits**:
    - **Modularity & Reusability**: Easily reuse resource patterns across different parts of your application or even different projects.
    - **Clear Ownership**: Each construct is responsible for a specific set of functionality (e.g., a `S3Construct` handles all S3 buckets for the stack, a `DynamoDbConstruct` handles DynamoDB tables).
    - **Maintainability**: Changes to a specific resource type are isolated within its construct file, making updates safer and easier to manage.
    - **Testability**: Custom constructs are easier to unit test in isolation.
- **Example (`lib/stateful/constructs/s3.ts`):**
    The `S3Construct` in the stateful stack handles the creation and configuration of S3 buckets (`dataBucket` and `assetsBucket`). It demonstrates how to apply environment-specific logic (e.g., `removalPolicy`) and expose public properties for other constructs or stacks to reference.

---

## How Environments Work

Environments are defined in `configs/` and instantiate the stacks via `bin/environments/`.

1. **Configuration (`configs/dev.ts`)**: Defines values specific to an environment (like `stage: 'dev'`, account IDs, regions, specific feature flags, or CORS origins).
2. **Environment Setup (`bin/environments/dev.ts`)**: Takes the configuration and passes it into `setupEnvironment` in `base.ts`.
3. **The Base Wiring (`bin/environments/base.ts`)**: This is the heart of the cross-stack communication. It creates the `StatefulStack`, and then creates the `StatelessStack`, passing the necessary constructs (like databases or buckets) from the stateful stack directly into the stateless stack's properties.

### Example: Passing Data
If you create an S3 bucket in `StatefulStack`, you expose it as a public property on the class:
```typescript
// lib/stateful/stateful-stack.ts
public dataBucket: s3.IBucket;
```
Then, in `bin/environments/base.ts`, you pass it to the Stateless Stack:
```typescript
// bin/environments/base.ts
dataBucket: statefulStack.dataBucket,
```

## Deployment

To deploy a specific environment, target its specific stacks. 

For development:
```bash
npx cdk deploy "template-dev-*"
```

For production:
```bash
npx cdk deploy "template-prod-*"
```

*(Note: The `template-dev` prefix is defined by the `stage` variable in the respective config file).*

## Development

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template