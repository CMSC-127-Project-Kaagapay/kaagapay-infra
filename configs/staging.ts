const commons = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  stage: "staging",
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
  },
};

export default {
  commons,
  Stateful,
  Stateless,
  Global,
};
