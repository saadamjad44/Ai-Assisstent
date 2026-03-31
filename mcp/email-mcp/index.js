/**
 * Email MCP Server for SAZA AI Employee
 * 
 * Provides tools for Claude Code to send and draft emails via Gmail API.
 * Follows Model Context Protocol specification.
 */

import { Server } from "@anthropic/mcp-sdk";
import { google } from "googleapis";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Configuration
const CREDENTIALS_PATH = path.join(__dirname, "../../scripts/credentials.json");
const TOKEN_PATH = path.join(__dirname, "../../scripts/token.json");
const SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly"
];

/**
 * Get authenticated Gmail client
 */
async function getGmailClient() {
    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, "utf8"));
    const { client_id, client_secret, redirect_uris } = credentials.installed || credentials.web;

    const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

    if (fs.existsSync(TOKEN_PATH)) {
        const token = JSON.parse(fs.readFileSync(TOKEN_PATH, "utf8"));
        oAuth2Client.setCredentials(token);
    } else {
        throw new Error("No token.json found. Run gmail_watcher.py first to authenticate.");
    }

    return google.gmail({ version: "v1", auth: oAuth2Client });
}

/**
 * Encode email to base64url format for Gmail API
 */
function encodeEmail(to, subject, body, cc = "", bcc = "") {
    const lines = [
        `To: ${to}`,
        `Subject: ${subject}`,
        `MIME-Version: 1.0`,
        `Content-Type: text/html; charset=utf-8`,
    ];

    if (cc) lines.push(`Cc: ${cc}`);
    if (bcc) lines.push(`Bcc: ${bcc}`);

    lines.push("", body);

    const email = lines.join("\r\n");
    return Buffer.from(email).toString("base64url");
}

// Create MCP Server
const server = new Server({
    name: "email-mcp",
    version: "1.0.0",
});

// Define tools
server.setToolHandler(async (request) => {
    const { name, arguments: args } = request;

    switch (name) {
        case "send_email": {
            try {
                const gmail = await getGmailClient();
                const raw = encodeEmail(args.to, args.subject, args.body, args.cc, args.bcc);

                const response = await gmail.users.messages.send({
                    userId: "me",
                    requestBody: { raw },
                });

                return {
                    success: true,
                    messageId: response.data.id,
                    message: `Email sent successfully to ${args.to}`,
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message,
                };
            }
        }

        case "draft_email": {
            try {
                const gmail = await getGmailClient();
                const raw = encodeEmail(args.to, args.subject, args.body, args.cc, args.bcc);

                const response = await gmail.users.drafts.create({
                    userId: "me",
                    requestBody: {
                        message: { raw },
                    },
                });

                return {
                    success: true,
                    draftId: response.data.id,
                    message: `Draft created successfully for ${args.to}`,
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message,
                };
            }
        }

        case "list_emails": {
            try {
                const gmail = await getGmailClient();
                const response = await gmail.users.messages.list({
                    userId: "me",
                    maxResults: args.maxResults || 10,
                    q: args.query || "is:unread",
                });

                const messages = response.data.messages || [];
                const emails = [];

                for (const msg of messages.slice(0, 5)) {
                    const full = await gmail.users.messages.get({
                        userId: "me",
                        id: msg.id,
                    });

                    const headers = full.data.payload.headers;
                    emails.push({
                        id: msg.id,
                        subject: headers.find(h => h.name === "Subject")?.value || "No Subject",
                        from: headers.find(h => h.name === "From")?.value || "Unknown",
                        date: headers.find(h => h.name === "Date")?.value || "",
                        snippet: full.data.snippet,
                    });
                }

                return {
                    success: true,
                    emails,
                };
            } catch (error) {
                return {
                    success: false,
                    error: error.message,
                };
            }
        }

        default:
            return { error: `Unknown tool: ${name}` };
    }
});

// Define available tools
server.setListToolsHandler(() => ({
    tools: [
        {
            name: "send_email",
            description: "Send an email via Gmail",
            inputSchema: {
                type: "object",
                properties: {
                    to: { type: "string", description: "Recipient email address" },
                    subject: { type: "string", description: "Email subject line" },
                    body: { type: "string", description: "Email body (HTML supported)" },
                    cc: { type: "string", description: "CC recipients (optional)" },
                    bcc: { type: "string", description: "BCC recipients (optional)" },
                },
                required: ["to", "subject", "body"],
            },
        },
        {
            name: "draft_email",
            description: "Create an email draft in Gmail (does not send)",
            inputSchema: {
                type: "object",
                properties: {
                    to: { type: "string", description: "Recipient email address" },
                    subject: { type: "string", description: "Email subject line" },
                    body: { type: "string", description: "Email body (HTML supported)" },
                    cc: { type: "string", description: "CC recipients (optional)" },
                    bcc: { type: "string", description: "BCC recipients (optional)" },
                },
                required: ["to", "subject", "body"],
            },
        },
        {
            name: "list_emails",
            description: "List recent emails from Gmail inbox",
            inputSchema: {
                type: "object",
                properties: {
                    query: { type: "string", description: "Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')" },
                    maxResults: { type: "number", description: "Maximum number of emails to return (default: 10)" },
                },
            },
        },
    ],
}));

// Start server
server.listen();
console.log("Email MCP Server started");
