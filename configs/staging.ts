const commons = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  stage: "template-staging",
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
    region: "us-east-1",
  },
};

export default {
  commons,
  Stateful,
  Stateless,
  Global,
};
