import meta from "../../../pages/_meta.ts";
import api_reference_meta from "../../../pages/api-reference/_meta.ts";
import benchmarks_meta from "../../../pages/benchmarks/_meta.ts";
import getting_started_meta from "../../../pages/getting-started/_meta.ts";
export const pageMap = [{
  data: meta
}, {
  name: "api-reference",
  route: "/api-reference",
  children: [{
    data: api_reference_meta
  }, {
    name: "index",
    route: "/api-reference",
    frontMatter: {
      "title": "API Reference",
      "description": "Complete Apollo RAG API documentation with interactive examples"
    }
  }]
}, {
  name: "benchmarks",
  route: "/benchmarks",
  children: [{
    data: benchmarks_meta
  }, {
    name: "overview",
    route: "/benchmarks/overview",
    frontMatter: {
      "title": "Benchmark Overview",
      "description": "Apollo RAG performance benchmarks and comparisons"
    }
  }]
}, {
  name: "getting-started",
  route: "/getting-started",
  children: [{
    data: getting_started_meta
  }, {
    name: "configuration",
    route: "/getting-started/configuration",
    frontMatter: {
      "sidebarTitle": "Configuration"
    }
  }, {
    name: "first-query",
    route: "/getting-started/first-query",
    frontMatter: {
      "sidebarTitle": "First Query"
    }
  }, {
    name: "installation",
    route: "/getting-started/installation",
    frontMatter: {
      "title": "Installation",
      "description": "Install Apollo RAG and set up your development environment"
    }
  }, {
    name: "quick-start",
    route: "/getting-started/quick-start",
    frontMatter: {
      "title": "Quick Start",
      "description": "Get Apollo RAG running in 5 minutes"
    }
  }]
}, {
  name: "index-new",
  route: "/index-new",
  frontMatter: {
    "title": "Apollo RAG - GPU-Accelerated Document Intelligence",
    "description": "Production-grade RAG platform with CUDA optimization, adaptive retrieval, and enterprise deployment"
  }
}, {
  name: "index",
  route: "/",
  frontMatter: {
    "title": "Apollo RAG - GPU-Accelerated Document Intelligence",
    "description": "10x faster RAG with GPU acceleration"
  }
}, {
  name: "playground",
  route: "/playground",
  frontMatter: {
    "title": "Interactive Code Playground",
    "description": "Try Apollo RAG API in your browser with our interactive code playground"
  }
}];