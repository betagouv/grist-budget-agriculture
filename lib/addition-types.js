const additionTypes = {
  date: {
    name: "Date",
    text: () => new Date().toLocaleDateString(),
    enabled: () => true,
  },
  city: {
    name: "City",
    text: (config) => config.city,
    enabled: (config) => config?.city?.length,
  },
  title: {
    name: "Title",
    text: (config) => config.title,
    enabled: (config) => config?.title?.length,
  },
  name: {
    name: "Name",
    text: (config) => config.name,
    enabled: (config) => config?.name?.length,
  },
  signature: {
    name: "Signature",
    enabled: (config) => {
      return config?.signature?.length;
    },
  },
};

export default additionTypes;
