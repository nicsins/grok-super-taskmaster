import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "test_node_support", version: "1.0.0" });

server.tool("health_check", "Health of the forged test_node_support connector (node podman mcp).", {}, async () => ({
  content: [{ type: "text", text: JSON.stringify({ status: "healthy (node podman mcp via forge)", service: "test_node_support", timestamp: new Date().toISOString() }) }]
}));

server.tool("execute_action", "Execute generic action on the forged connector.", {
  action: z.string().describe("Action name from capabilities"),
  params: z.record(z.any()).optional().describe("Params for the action")
}, async ({ action, params = {} }) => ({
  content: [{ type: "text", text: JSON.stringify({ action, result: "executed via wired node forge connector", params, note: "Extend server.js or use real impl for production." }) }]
}));

server.tool("list_capabilities", "List capabilities of this forged connector.", {}, async () => ({
  content: [{ type: "text", text: JSON.stringify(["health_check", "execute_action", "list_capabilities"]) }]
}));

const transport = new StdioServerTransport();
await server.connect(transport);
