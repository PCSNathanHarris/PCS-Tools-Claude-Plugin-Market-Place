# SOP: Installing the PCS Tools Plugins in Claude Code
**Version:** 2.0 | **Marketplace:** `pcs-tools` | **Plugins:** `pcs-promo-parser` v1.0.0, `pcs-map-updater` v1.0.0
**Applies To:** All PCS team members using the Kit Builder and MAP pricing workflows
**Maintained By:** Nathan Harris (nathan.harris@pcstools.com)

---

## Overview

This SOP walks you through installing **Claude Code** (the terminal version of Claude) and the **PCS Promo Parser plugin** on your Windows machine. Once set up, the plugin will update automatically every time you open Claude — you will never need to run these setup steps again.

**Estimated time:** 10–15 minutes for a first-time install.

---

## Prerequisites

- Windows 10 or Windows 11
- Internet connection
- A Claude.ai account (**Pro or Max plan required** — free accounts cannot use Claude Code)
  - If you do not have one, go to [claude.ai](https://claude.ai) and sign up, then upgrade your plan before continuing.

---

## Part 1 — Install Node.js

Claude Code runs on Node.js. You only need to do this once per machine.

**1.1** Open **PowerShell** as a normal user (no need to run as Administrator).
- Press `Win + S`, type `PowerShell`, click **Windows PowerShell**.

**1.2** Check if Node.js is already installed:
```powershell
node --version
```
- If you see a version number like `v20.x.x` or higher, **skip to Part 2**.
- If you see an error like `'node' is not recognized`, continue with step 1.3.

**1.3** Install Node.js using Windows Package Manager:
```powershell
winget install OpenJS.NodeJS.LTS
```
- Accept any prompts that appear. The install takes 1–3 minutes.

**1.4** Close PowerShell completely, then reopen it. Verify Node.js installed correctly:
```powershell
node --version
npm --version
```
Both commands should return version numbers. If either still errors, restart your computer and try again.

---

## Part 2 — Install Claude Code

**2.1** In PowerShell, run:
```powershell
npm install -g @anthropic-ai/claude-code
```
This installs the Claude Code CLI globally on your machine. It takes about 1 minute.

**2.2** Verify the install:
```powershell
claude --version
```
You should see a version number printed. If you see `'claude' is not recognized`, close and reopen PowerShell, then try again.

---

## Part 3 — First-Time Login

**3.1** Start Claude Code:
```powershell
claude
```

**3.2** The first time you run this, Claude Code will ask you to log in. It will open a browser window automatically.
- Log in with your **Claude.ai account** (the same email/password you use on claude.ai).
- After logging in, return to PowerShell. You will see the Claude Code prompt.

> **Note:** If the browser does not open automatically, copy the URL printed in PowerShell and paste it into your browser manually.

**3.3** You are now inside a Claude Code session. The prompt looks like:
```
>
```
You can type messages to Claude here, or use slash commands (which start with `/`).

---

## Part 4 — Install the PCS Tools Plugins

Run these commands one at a time inside your Claude Code session (at the `>` prompt).

**4.1** Add the PCS Tools plugin marketplace:
```
/plugin marketplace add PCSNathanHarris/PCS-Tools-Claude-Plugin-Market-Place
```
Wait for the confirmation message before continuing.

**4.2** Install the Promo Parser plugin:
```
/plugin install pcs-promo-parser
```
Wait for the confirmation message.

**4.3** Install the MAP Updater plugin:
```
/plugin install pcs-map-updater
```
Wait for the confirmation message.

**4.4** Verify both plugins installed:
```
/plugin
```
This opens the plugin menu. You should see **pcs-promo-parser v1.0.0** AND **pcs-map-updater v1.0.0** listed under the **Installed** tab.

Press `Esc` to close the menu.

> **Note for existing users:** if you previously installed from the older `PCSNathanHarris/pcs-promo-parser` or `PCSNathanHarris/pcs-map-updater` repos, first remove those marketplaces:
> ```
> /plugin marketplace remove pcs-tools
> /plugin marketplace remove pcs-map-updater
> ```
> Then run the steps above. This ensures you're on the unified marketplace going forward.

---

## Part 5 — Enable Auto-Updates

This step ensures you always have the latest version without doing anything manually.

**5.1** Open the plugin menu:
```
/plugin
```

**5.2** Use the arrow keys or `Tab` to navigate to the **Marketplaces** tab.

**5.3** Highlight **pcs-tools** and press `Enter` to open it.

**5.4** Find the **Auto-update** toggle and press `Enter` or `Space` to turn it **ON**.

**5.5** Press `Esc` to close the menu.

That's it. From now on, every time you start `claude`, it will automatically check for and install any new version of the plugin in the background.

---

## Part 6 — Using the Plugin

**6.1** Start a Claude Code session in PowerShell:
```powershell
claude
```

**6.2** Run the promo deck parser by typing:
```
/parse-promo-deck
```
Claude will guide you through providing the PDF and any other required inputs.

Output files will be placed in the working directory where you started `claude`, named in the format `<Vendor>-<Q#>-<YYYY>-<Type>.csv` — for example `DeWalt-Q2-2026-Promo-List.csv`.

**6.3** Or run the MAP price updater by typing:
```
/map-price-update
```
Claude will ask for the manufacturer MAP sheet, the NetSuite ERP export, and which columns to use for SKU and MAP. The output is an Excel workbook with four sheets (MAP Update Review, Exceptions, All Manufacturer Rows, Summary) saved in the same directory as the manufacturer file.

---

## Part 7 — Starting Claude Code in the Future

After the one-time setup above, starting a session is just:

**7.1** Open PowerShell.

**7.2** Navigate to the folder where you want your output files saved:
```powershell
cd "C:\path\to\your\output\folder"
```

**7.3** Start Claude:
```powershell
claude
```

Auto-update runs silently on startup — you do not need to do anything else to stay current.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `'claude' is not recognized` after install | Close and reopen PowerShell. If it persists, restart your computer. |
| Browser login page doesn't open | Copy the URL from PowerShell and paste it into Chrome manually. |
| Plugin menu shows an old version after an update was released | Type `/plugin marketplace update pcs-tools` to force a refresh. |
| `npm install` fails with a permissions error | Do NOT run PowerShell as Administrator. Run it as a normal user. |
| Claude asks for an API key | You need a Claude Pro or Max subscription at claude.ai — free accounts do not work with Claude Code. |
| Plugin not found after `/plugin marketplace add` | Confirm the repo is public at github.com/PCSNathanHarris/PCS-Tools-Claude-Plugin-Market-Place, then retry. |

---

## Quick Reference — All Commands

```powershell
# One-time setup (run in PowerShell)
winget install OpenJS.NodeJS.LTS          # Install Node.js
npm install -g @anthropic-ai/claude-code  # Install Claude Code
claude                                     # First launch + login
```

```
# Inside Claude Code (one-time plugin setup)
/plugin marketplace add PCSNathanHarris/PCS-Tools-Claude-Plugin-Market-Place
/plugin install pcs-promo-parser
/plugin install pcs-map-updater
/plugin   <-- go to Marketplaces > pcs-tools > Auto-update ON
```

```powershell
# Every day use
cd "C:\path\to\output\folder"
claude
```

```
# Inside Claude Code (daily use)
/parse-promo-deck    # parses a vendor promo deck PDF
/map-price-update    # merges a vendor MAP sheet with the ERP export
```

---

*For questions or issues, contact Nathan Harris at nathan.harris@pcstools.com.*
