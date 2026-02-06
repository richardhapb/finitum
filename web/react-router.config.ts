export default {
  ssr: false,
  async prerender() {
    return ["/", "/guide", "/terms", "/privacy"];
  },
};
