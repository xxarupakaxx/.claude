import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

export function createServer(): McpServer {
  const server = new McpServer({
    name: "workflow-html-app",
    version: "0.1.0",
  });

  // Register view-plan tool
  server.tool(
    "view-plan",
    "計画ファイル（30_plan.md）をインタラクティブHTMLで表示。Markdownコンテンツを渡すとHTML UIで可視化",
    {
      content: z.string().describe("Markdownコンテンツ"),
    },
    async ({ content }) => {
      // Return the content as-is; the UI will render it
      return {
        content: [
          {
            type: "text",
            text: content,
          },
        ],
        // MCP Apps metadata to link to UI
        _meta: {
          ui: {
            resourceUri: "ui://plan-viewer/index.html",
          },
        },
      };
    }
  );

  // Register UI resource for plan-viewer
  server.resource(
    "plan-viewer-ui",
    new ResourceTemplate("ui://plan-viewer/{path}", { list: undefined }),
    async (uri) => {
      // For now, return the HTML content inline
      // In production, this would be bundled by Vite
      const htmlPath = join(__dirname, "ui", "plan-viewer.html");

      try {
        const htmlContent = readFileSync(htmlPath, "utf-8");
        return {
          contents: [
            {
              uri: uri.href,
              mimeType: "text/html",
              text: htmlContent,
            },
          ],
        };
      } catch {
        return {
          contents: [
            {
              uri: uri.href,
              mimeType: "text/html",
              text: "<html><body><h1>Plan Viewer</h1><p>Loading...</p></body></html>",
            },
          ],
        };
      }
    }
  );

  // Register view-log tool
  server.tool(
    "view-log",
    "作業ログ（05_log.md）をインタラクティブHTMLで表示。Markdownコンテンツを渡すとLog Viewerで可視化",
    {
      content: z.string().describe("Markdownコンテンツ"),
    },
    async ({ content }) => {
      return {
        content: [{ type: "text", text: content }],
        _meta: {
          ui: {
            resourceUri: "ui://log-viewer/index.html",
          },
        },
      };
    }
  );

  server.resource(
    "log-viewer-ui",
    new ResourceTemplate("ui://log-viewer/{path}", { list: undefined }),
    async (uri) => {
      const htmlPath = join(__dirname, "ui", "plan-viewer.html");

      try {
        const htmlContent = readFileSync(htmlPath, "utf-8");
        return {
          contents: [{ uri: uri.href, mimeType: "text/html", text: htmlContent }],
        };
      } catch {
        return {
          contents: [{
            uri: uri.href,
            mimeType: "text/html",
            text: "<html><body><h1>Log Viewer</h1><p>Loading...</p></body></html>",
          }],
        };
      }
    }
  );

  // Register view-diagram tool
  server.tool(
    "view-diagram",
    "Mermaid図と任意のGraph JSONをインタラクティブHTMLで表示。Mermaidのズーム・パン、2.5Dレイヤービュー、Graph JSON timeline再生に対応",
    {
      mermaidCode: z.string().describe("Mermaidダイアグラムコード"),
      title: z.string().optional().describe("図のタイトル（オプション）"),
      graphJson: z.string().optional().describe("2.5Dレイヤービュー用のGraph JSON（オプション）"),
    },
    async ({ mermaidCode, title, graphJson }) => {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ mermaidCode, title: title || "Diagram", graphJson }),
          },
        ],
        _meta: {
          ui: {
            resourceUri: "ui://diagram-viewer/index.html",
          },
        },
      };
    }
  );

  // Register UI resource for diagram-viewer
  server.resource(
    "diagram-viewer-ui",
    new ResourceTemplate("ui://diagram-viewer/{path}", { list: undefined }),
    async (uri) => {
      const htmlPath = join(__dirname, "ui", "diagram-viewer.html");

      try {
        const htmlContent = readFileSync(htmlPath, "utf-8");
        return {
          contents: [
            {
              uri: uri.href,
              mimeType: "text/html",
              text: htmlContent,
            },
          ],
        };
      } catch {
        return {
          contents: [
            {
              uri: uri.href,
              mimeType: "text/html",
              text: "<html><body><h1>Diagram Viewer</h1><p>Loading...</p></body></html>",
            },
          ],
        };
      }
    }
  );

  // Register view-verification tool
  server.tool(
    "view-verification",
    "検証ガイド（90_verification.md）をインタラクティブHTMLで表示。チェックリストの進捗トラッキング付き",
    {
      content: z.string().describe("Markdownコンテンツ"),
    },
    async ({ content }) => {
      return {
        content: [
          {
            type: "text",
            text: content,
          },
        ],
        _meta: {
          ui: {
            resourceUri: "ui://verification-viewer/index.html",
          },
        },
      };
    }
  );

  // Register UI resource for verification-viewer
  server.resource(
    "verification-viewer-ui",
    new ResourceTemplate("ui://verification-viewer/{path}", { list: undefined }),
    async (uri) => {
      const htmlPath = join(__dirname, "ui", "verification-viewer.html");

      try {
        const htmlContent = readFileSync(htmlPath, "utf-8");
        return {
          contents: [
            {
              uri: uri.href,
              mimeType: "text/html",
              text: htmlContent,
            },
          ],
        };
      } catch {
        return {
          contents: [
            {
              uri: uri.href,
              mimeType: "text/html",
              text: "<html><body><h1>Verification Guide</h1><p>Loading...</p></body></html>",
            },
          ],
        };
      }
    }
  );

  return server;
}
