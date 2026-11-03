window.shadlet.loadExtension({
  name: "browser_fixture",
  version: "1.0.0",
  components: {
    Notice: ({ props }) => {
      const [ready] = window.React.useState(true);
      return window.React.createElement(
        "p",
        { "data-testid": "extension", className: "browser-fixture-notice" },
        ready ? String(props.message) : "not ready",
      );
    },
  },
});
