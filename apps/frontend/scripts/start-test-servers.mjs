import http from "http";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, resolve } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const apiPort = Number(process.env.MOCK_API_PORT ?? 4000);
const nextPort = Number(process.env.NEXT_PORT ?? 3000);

const server = http.createServer((req, res) => {
  if (!req.url) {
    res.writeHead(400);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${apiPort}`);

  if (req.method === "POST" && url.pathname === "/upload") {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(
        JSON.stringify({
          status: "stored",
          raw_data_id: 1,
          run_id: 123,
          workflow_started: true,
        }),
      );
    });
    return;
  }

  if (req.method === "GET" && url.pathname === "/dashboard/reports") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify([]));
    return;
  }

  if (req.method === "GET" && url.pathname === "/dashboard/violations") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify([]));
    return;
  }

  if (req.method === "GET" && url.pathname === "/dashboard/runs") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify([
        {
          id: 123,
          raw_id: 1,
          status: "completed",
          created_at: new Date().toISOString(),
          duration_seconds: 4.2,
        },
      ]),
    );
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "not_found" }));
});

server.listen(apiPort, () => {
  console.log(`Mock API server listening on ${apiPort}`);
});

const nextCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const nextProcess = spawn(nextCommand, ["run", "dev", "--", "-p", `${nextPort}`], {
  cwd: resolve(__dirname, ".."),
  stdio: "inherit",
  env: {
    ...process.env,
    NEXT_PUBLIC_API_URL: `http://localhost:${apiPort}`,
    NEXT_PUBLIC_AUTH_TOKEN: "test-token",
  },
});

const shutdown = () => {
  server.close();
  if (!nextProcess.killed) {
    nextProcess.kill("SIGTERM");
  }
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
process.on("exit", shutdown);

nextProcess.on("exit", (code) => {
  shutdown();
  process.exit(code ?? 0);
});
