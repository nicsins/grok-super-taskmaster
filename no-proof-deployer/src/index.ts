import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Tools will be imported here as we build them
import { prepareProductionApp, generateLegalDocs } from "./tools/prepareProductionApp.js";
import { setupStripeConnect } from "./tools/setupStripeConnect.js";
import { fullProductionDeploy } from "./tools/fullProductionDeploy.js";
import { configureCustomDomain, fullSymbioticConnectDomain, deployToVercelReal, provisionNeonReal, updateGodaddyDns, listGodaddyDns } from "./tools/configureCustomDomain.js";

const server = new McpServer({
  name: "no-proof-deployer",
  version: "0.1.0",
  description: "Takes any GitHub repo and turns it into a production-grade service on a custom domain with automatic 12% fee collection via Stripe Connect.",
});

// Register tools
server.tool(
  "prepare_production_app",
  "Adds all production files (vercel.json, Stripe Connect skeleton, webhook, metadata, legal footer) to a Next.js app so it is ready for no-proof-claims.com style deployment.",
  {
    repoPath: z.string().describe("Absolute path to the local clone of the GitHub repo"),
    appName: z.string().describe("Human readable name of the app (e.g. 'No Proof Claims')"),
    domain: z.string().describe("Final production domain (e.g. no-proof-claims.com)"),
  },
  async ({ repoPath, appName, domain }) => {
    const result = await prepareProductionApp(repoPath, appName, domain);
    return {
      content: [{ type: "text", text: result }],
    };
  }
);

server.tool(
  "setup_stripe_connect",
  "Generates Stripe Connect integration files and instructions so the app can collect a 12% success fee automatically on real payouts.",
  {
    repoPath: z.string(),
  },
  async ({ repoPath }) => {
    const result = await setupStripeConnect(repoPath);
    return {
      content: [{ type: "text", text: result }],
    };
  }
);

server.tool(
  "full_production_deploy",
  "Single orchestrator that prepares ANY app for production on a custom domain with 12% Stripe Connect fee collection. This is the recommended entry point for new apps.",
  {
    repoPath: z.string().describe("Absolute path to the cloned repo"),
    appName: z.string().describe("Display name (e.g. 'No Proof Claims')"),
    domain: z.string().describe("Final production domain (e.g. no-proof-claims.com)"),
  },
  async ({ repoPath, appName, domain }) => {
    const result = await fullProductionDeploy(repoPath, appName, domain);
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
  }
);

server.tool(
  "configure_custom_domain",
  "Generates exact DNS records and Vercel steps to point a custom domain (e.g. no-proof-claims.com) to a Vercel deployment. Supports GoDaddy and Cloudflare. When GODADDY_API_KEY/SECRET + VERCEL_TOKEN are present in the environment (or passed via Podman -e), performs the REAL symbiotic DNS update on GoDaddy + registers domain on Vercel project automatically. This is the effector used by high-level /task: {connect_domain; <url>} TASKs (see ~/.grok/tasks/connect_domain.task.json and workdir/task-orchestration/). Prefer standalone godaddy-mcp (podman-isolated) for pure DNS ops in orchestrator; this tool provides legacy/manual fallback + full-deploy integration.",
  {
    repoPath: z.string(),
    domain: z.string(),
    vercelProjectIdOrSlug: z.string().optional(),
  },
  async ({ repoPath, domain, vercelProjectIdOrSlug }) => {
    const result = await configureCustomDomain(repoPath, domain, vercelProjectIdOrSlug);
    return {
      content: [{ type: "text", text: result }],
    };
  }
);

// NEW ENHANCED real API tools for vercel deploy, godaddy DNS (TS port of godaddy-mcp/taskmaster logic), full symbiotic, neon.
server.tool(
  "deploy_to_vercel_real",
  "REAL Vercel deployment via direct API (POST /v13/deployments) when VERCEL_TOKEN present. Exercises production target deploy (dummy creds show exact API response path). For git-connected projects often a push suffices; this provides the API effector.",
  {
    projectIdOrSlug: z.string().describe("Vercel project id or slug"),
    gitRef: z.string().optional().describe("git ref/branch, default main"),
    teamId: z.string().optional(),
  },
  async ({ projectIdOrSlug, gitRef, teamId }) => {
    const result = await deployToVercelReal(projectIdOrSlug, gitRef || 'main', teamId);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "update_godaddy_dns",
  "REAL GoDaddy DNS record update (PATCH or PUT) using ported logic from godaddy-mcp.js / taskmaster-mcp. Supports arbitrary records array. Requires GODADDY_API_KEY + SECRET in env (or podman -e). Used by full_symbiotic and production_domain_connect.",
  {
    domain: z.string(),
    records: z.array(z.object({
      type: z.string(),
      name: z.string(),
      data: z.string(),
      ttl: z.number().optional().default(600),
    })).describe("Array of DNS records e.g. [{type:'A',name:'@',data:'76.76.21.21',ttl:600}]"),
    mode: z.enum(['add', 'replace']).optional().default('add'),
  },
  async ({ domain, records, mode }) => {
    const result = await updateGodaddyDns(domain, records as any, mode);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }
);

server.tool(
  "full_symbiotic_connect_domain",
  "High-level REAL symbiotic domain connector: applies Vercel-recommended DNS to GoDaddy via real API + registers domain on Vercel project if token. Optional trigger deploy. This is the direct enhanced implementation (no external godaddy-mcp required) used by production_domain_connect TASK. Dummy creds ok for path verification.",
  {
    domain: z.string().describe("e.g. example.com"),
    vercelProjectIdOrSlug: z.string().optional(),
    triggerDeploy: z.boolean().optional().default(false),
  },
  async ({ domain, vercelProjectIdOrSlug, triggerDeploy }) => {
    const result = await fullSymbioticConnectDomain(domain, vercelProjectIdOrSlug, triggerDeploy);
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "provision_neon_db",
  "Provision (or stub) a Neon Postgres project via real API when NEON_API_KEY present. Uses https to api.neon.tech (no SDK for admin). Returns conn info note. @neondatabase/serverless (already in deps) for runtime queries post-provision. Integrates with full deploy flows.",
  {
    projectName: z.string(),
    region: z.string().optional().default('aws-us-east-1'),
  },
  async ({ projectName, region }) => {
    const result = await provisionNeonReal(projectName, region);
    return { content: [{ type: "text", text: result }] };
  }
);

// NEW: expose listGodaddyDns (already real impl) + generate_legal_docs (real file writer for legal footer/pages with 12% disclosure)
server.tool(
  "list_godaddy_dns",
  "REAL list of current DNS records for a domain via GoDaddy API (GET /v1/domains/{domain}/records) when GODADDY_API_KEY/SECRET present in env/podman. Returns wouldCall + error if no creds. Used for pre/post verification in symbiotic domain connects and production_domain_connect TASK.",
  {
    domain: z.string().describe("The domain to query e.g. example.com"),
    type: z.string().optional().describe("Optional filter e.g. A or CNAME"),
    name: z.string().optional().describe("Optional name filter e.g. @ or www"),
  },
  async ({ domain, type, name }) => {
    const result = await listGodaddyDns(domain, type, name);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  }
);

server.tool(
  "generate_legal_docs",
  "Generates real LEGAL.md + Next.js /terms and /privacy pages + components/LegalFooter.tsx (with explicit 12% fee disclosure, links, and compliance notes). Called automatically by prepare_production_app; also standalone for existing apps. Writes production-ready files to repoPath.",
  {
    repoPath: z.string().describe("Absolute path to the local clone of the GitHub repo"),
    appName: z.string().describe("Human readable name of the app (e.g. 'No Proof Claims')"),
    domain: z.string().describe("Final production domain (e.g. no-proof-claims.com)"),
  },
  async ({ repoPath, appName, domain }) => {
    const result = await generateLegalDocs(repoPath, appName, domain);
    return { content: [{ type: "text", text: result }] };
  }
);

// More tools will be added: configure_domain, provision_neon, deploy_to_vercel, etc. (generate_legal_docs + list_godaddy_dns now added as real tools)
// See also: dedicated godaddy MCP at workdir/task-orchestration/godaddy-mcp/ (real podman MCP with list_dns, set_dns_records, verify_propagation per GoDaddy + Vercel symbiotic protocol). This no-proof-deployer now has native TS real-API versions for tight integration.

const transport = new StdioServerTransport();
await server.connect(transport);

console.log("no-proof-deployer MCP server running");