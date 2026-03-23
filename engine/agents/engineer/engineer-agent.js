const fs = require("fs");
const path = require("path");

class EngineerAgent {
  constructor(options = {}) {
    this.agentId = "engineer";
    this.rootDir = options.rootDir || __dirname;
    this.configPath = path.join(this.rootDir, "engineer-config.json");
    this.promptPath = path.join(
      this.rootDir,
      "prompts",
      "engineer-system.prompt.txt"
    );

    this.config = this.loadJson(this.configPath);
    this.systemPrompt = this.loadText(this.promptPath);

    this.model = this.config.model || "gpt-5.4";
    this.temperature = Number(this.config.temperature ?? 0.2);
    this.maxOutputTokens = Number(this.config.maxOutputTokens ?? 1800);
  }

  loadJson(filePath) {
    try {
      return JSON.parse(fs.readFileSync(filePath, "utf-8"));
    } catch (error) {
      console.error(`[EngineerAgent] Failed to load JSON: ${filePath}`, error);
      return {};
    }
  }

  loadText(filePath) {
    try {
      return fs.readFileSync(filePath, "utf-8");
    } catch (error) {
      console.error(`[EngineerAgent] Failed to load text: ${filePath}`, error);
      return "You are EngineerAgent.";
    }
  }

  validateEnv() {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return {
        ok: false,
        error: "OPENAI_API_KEY is missing in environment."
      };
    }
    return { ok: true };
  }

  async runTask(input) {
    const envCheck = this.validateEnv();
    if (!envCheck.ok) {
      return {
        ok: false,
        agent: this.agentId,
        error: envCheck.error
      };
    }

    if (!input || typeof input !== "object") {
      return {
        ok: false,
        agent: this.agentId,
        error: "Input must be an object."
      };
    }

    const userPrompt = String(input.prompt || "").trim();
    if (!userPrompt) {
      return {
        ok: false,
        agent: this.agentId,
        error: "Prompt is required."
      };
    }

    const response = await this.callOpenAI(userPrompt, input.context || {});
    return {
      ok: true,
      agent: this.agentId,
      model: this.model,
      output: response
    };
  }

  async callOpenAI(userPrompt, context = {}) {
    const apiKey = process.env.OPENAI_API_KEY;

    const payload = {
      model: this.model,
      input: [
        {
          role: "system",
          content: [
            {
              type: "input_text",
              text: this.systemPrompt
            }
          ]
        },
        {
          role: "user",
          content: [
            {
              type: "input_text",
              text: this.buildUserMessage(userPrompt, context)
            }
          ]
        }
      ],
      temperature: this.temperature,
      max_output_tokens: this.maxOutputTokens
    };

    const response = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`OpenAI API error: ${response.status} ${text}`);
    }

    const data = await response.json();
    return this.extractText(data);
  }

  buildUserMessage(userPrompt, context) {
    return [
      `Task: ${userPrompt}`,
      "",
      "Context:",
      JSON.stringify(context, null, 2)
    ].join("\n");
  }

  extractText(data) {
    if (!data) return "";
    if (typeof data.output_text === "string" && data.output_text.trim()) {
      return data.output_text.trim();
    }

    const parts = [];
    const output = Array.isArray(data.output) ? data.output : [];
    for (const item of output) {
      const content = Array.isArray(item.content) ? item.content : [];
      for (const c of content) {
        if (c.type === "output_text" && c.text) {
          parts.push(c.text);
        }
      }
    }

    return parts.join("\n").trim();
  }
}

module.exports = EngineerAgent;