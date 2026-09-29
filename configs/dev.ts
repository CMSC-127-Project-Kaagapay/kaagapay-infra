const commons = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT || "111111111111",
    region: process.env.CDK_DEFAULT_REGION || "ap-southeast-1",
  },
  stage: "dev",
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
