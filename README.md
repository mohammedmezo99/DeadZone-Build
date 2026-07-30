# DeadZone Build

Public GitHub Actions launcher for the DeadZone build ecosystem.

## Architecture

```text
Telegram / GitHub Actions
          ↓
  DeadZone-Build (PUBLIC)
          ↓
  one bootstrap credential
          ↓
DeadZone-Secrets (PRIVATE)
          ↓
config + rclone + runtime helpers
          ↓
private DeadZone engine
          ↓
Build → Pack → Verify → Upload
```

The public launcher owns workflow orchestration only. Private engines, shared runtime values, cloud configuration and helper runtime files belong to `mohammedmezo99/DeadZone-Secrets` or the relevant private engine repository.

## Workflows

- `MEZO_Lite.yml` — DeadZone Lite
- `gamingplus.yml` — DeadZone GamingPlus
- `DeadZone_Port.yml` — DeadZone Port dual-ROM pipeline
- `legend.yml` — DeadZone Legend
- `ninja.yml` — DeadZone Ninja
- `frameworkpatcher.yml` — DeadZone FrameworkPatcher

The existing input models and build paths remain edition-specific. In particular, Port keeps its Stock ROM + Port/Donor ROM contract.

## Central runtime

The launcher loads current values from the private repository on every build. Repository routing is defined centrally, so moving or renaming an engine does not require editing every workflow.

Canonical private runtime source:

```text
mohammedmezo99/DeadZone-Secrets
```

After migration, the launcher requires only one private-repository bootstrap credential. The canonical name is:

```text
DEADZONE_PRIVATE_TOKEN
```

For transition compatibility, the one-shot migration also accepts the existing `PRIVATE_REPO_TOKEN` or `GH_TOKEN` as the bootstrap credential.

## Private engines

```text
mohammedmezo99/DeadZone_Lite
mohammedmezo99/DeadZone_GamingPlus
mohammedmezo99/DeadZone_Port
mohammedmezo99/DeadZone_Legend
mohammedmezo99/DeadZone_Ninja
mohammedmezo99/DeadZone_FrameworkPatcher
mohammedmezo99/FrameworkPatcherModule
```

## Control Bot

Control Bot dispatches opaque request IDs to this launcher. Private request data is resolved through the existing signed DeadZone contract; the central-runtime migration does not change that build contract.
