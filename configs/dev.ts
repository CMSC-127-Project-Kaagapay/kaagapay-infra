const commons = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  stage: "template-dev",
};

const Stateful = {
  ...commons,
  env: {
    ...commons.env,
  },
};

const Stateless = {
  ...commons,
  env: {
    ...commons.env,
  },
  corsOrigins: ["*"],
};

const Global = {
  ...commons,
  env: {
    ...commons.env,
    region: "us-east-1", // Keep us-east-1 for global resources like CloudFront certificates
  },
};

export default {
  commons,
  Stateful,
  Stateless,
  Global,
};
