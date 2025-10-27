import meta from "../../../pages/_meta.ts";
import benchmarks_meta from "../../../pages/benchmarks/_meta.ts";
import getting_started_meta from "../../../pages/getting-started/_meta.ts";
export const pageMap = [{
  data: meta
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
    name: "installation",
    route: "/getting-started/installation",
    frontMatter: {
      "title": "Installation",
      "description": "Install Apollo RAG and set up your development environment"
    }
  }]
}, {
  name: "index",
  route: "/",
  frontMatter: {
    "title": "Apollo RAG - GPU-Accelerated Document Intelligence",
    "description": "Production-grade RAG platform with CUDA optimization, adaptive retrieval, and enterprise deployment"
  }
}];