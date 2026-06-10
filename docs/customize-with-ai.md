# Customize Adam Prism Using Any AI Tool

You do not need to be a programmer to customize Adam. You can use ChatGPT, Claude, DeepSeek, Gemini — any AI assistant — to help you configure and extend the platform. Once you have it set up the way you want, you can phase those tools out and use Adam directly.

This guide shows you how.

---

## Principle

Adam's configuration is JSON files and its extensions are Python files. AI tools are excellent at both. You describe what you want in plain language, they generate the configuration or code, you paste it in. No programming knowledge required.

---

## Common customizations

### 1. Change the personality

Adam reads its personality from a configuration file. Tell any AI tool:

```
I use Adam Prism, an open-source AI platform. Its personality is configured in
a JSON file. I want my Adam to speak formally, prefer Islamic references,
and respond in short paragraphs. Generate the personality config block I
should use.
```

The AI will output a JSON block. Copy it into your configuration file at `~/.adam/config.json`.

### 2. Remove channels you do not need

By default Adam enables 25 communication channels. If you only use Telegram, tell an AI:

```
I use Adam Prism with 25 communication channels. I only need Telegram.
Show me the minimal channels config that enables Telegram and disables
everything else. One channel only.
```

Paste the generated config into `~/.adam/channels.json`.

### 3. Add a custom tool

Tools are Python files in `adam/tools/custom/`. You do not need to write the code yourself. Describe your need:

```
I want Adam to be able to check the weather. I need a tool that takes a city
name and returns the current weather using OpenWeatherMap's free API. Generate
the Python file for this Adam Prism tool, with the tool registration format
used by the project.
```

Save the generated file to `adam/tools/custom/weather.py`. Adam will load it automatically.

### 4. Add a new communication channel

```
I want Adam to communicate via SMS using Twilio. Generate the channel adapter
file following Adam's channel pattern. Include configuration options for
account_sid, auth_token, and phone_number.
```

Save to `adam/channels/custom/sms.py`.

---

## Step by step: a complete example

**Goal:** Customize Adam to be a private research assistant focused on medical papers.

1. Open ChatGPT, Claude, or DeepSeek.
2. Paste:

```
I am setting up Adam Prism as a medical research assistant. I need three things:
1. A personality config that makes it reference recent papers, avoid speculation,
   and cite sources.
2. Disable all channels except local web chat.
3. Enable the web search and file system tools only, disable everything else.
```

3. Copy the generated JSON and file changes.
4. Apply them to your Adam configuration.
5. Test:

```bash
python main.py --port 8001
curl http://localhost:8001/api/chat -d '{"message":"What is the latest on mRNA vaccines?"}'
```

6. If something is wrong, paste the error back to the AI tool and ask for a fix.

---

## After customization: phase out the helper

Once Adam behaves the way you want, you have two options:

- Keep using the AI tool when you want to make major changes.
- Ask Adam itself to help you modify its own configuration:

```
Adam, I want you to change your response style to be more direct.
What config field should I modify?
```

Adam can read and suggest changes to its own configuration files. It will not modify them without confirmation.

---

## Tips

- **Save your prompts.** When you find a prompt that works well, save it. You may need it again.
- **One change at a time.** Make one customization, test it, then move to the next. This makes debugging trivial.
- **Use version control.** Before making changes, run `git init && git add . && git commit -m "before changes"`. If something breaks, you can revert.
- **Ask for rollback instructions.** When asking an AI to generate a change, also ask: "How do I undo this if something goes wrong?"

---

## Why this works

Adam's architecture is modular by design. Every component has a clear interface and lives in its own file. AI tools trained on open-source code understand these patterns. They can generate valid configurations and extensions without you writing a single line of code from scratch.

The irony is not lost on us: you use other AI tools to customize Adam, and once Adam is set up, you no longer need them. That is the point. Adam is the last AI tool you will need to configure.
