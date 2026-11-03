---
status: review
story: 1.1 du run « dépôts publics sans charte d'origine »
version: 2.0.0
---

# HarnessLab 2.0.0 : nom et charte génériques

Source : brief commun des stories 1.x, `regles-debrand.md` et `charte-generique.md` (section du dépôt), dépôt d'orchestration.
Objectif : rendre la version publique générique. Le dépôt, le paquet, la CLI, les variables et le dossier de données sont renommés, et la charte générique est appliquée. L'historique est conservé.

## Fait

- Renommage : `src/wavestack` → `src/harness_lab` (`git mv`), CLI `harness-lab`, `harness-lab.toml`, dossiers de spec `spec-harness-lab-*`, `tools/e2e/harness_lab_e2e.py`, `docs/assets/harness-lab-demo.*`, URLs `Aliquanto3/harness-lab`, textes fr, en et de. Pas d'alias de l'ancienne commande.
- Compatibilité (`src/harness_lab/compat.py`) : `getenv("HARNESS_LAB_X")` lit `WAVESTACK_X` en repli, avec un seul `DeprecationWarning` par variable. `migrate_data_dir` copie l'ancien dossier de données vers le nouveau, en passant par un dossier intermédiaire, si le nouveau n'existe pas encore ; il ne supprime jamais l'ancien. `config.data_dir()` s'en sert. Les installeurs (`install.sh`, `install.ps1`) lisent les anciennes variables en repli, avec un avertissement, et copient l'ancien dossier par défaut (sauf en mode à blanc). Le banc `v2s6` lit `WAVESTACK_LLAMA_SERVER` en repli.
- Charte : nouvelles valeurs dans `tokens.css` et `DESIGN.md` (frontmatter, tableaux, contrastes) ; nouveau jeton `on-status` (équivalent de `sur-statut` dans la charte) pour le texte sur succès, erreur et accent ; pictogramme devant le nom dans la barre des six pages ; favicon de la charte. Les épingles de contraste de `tests/test_web_tokens.py` ont été recalculées. Les logos d'éditeurs sont gardés.
- Marque d'origine retirée de `_bmad-output` : informations internes, validations, hébergement, collègues et clients. La forge commerciale V2 et le brainstorm du nom sont supprimés. Les maquettes `.working` reçoivent le pictogramme. Seules restent les citations du papier de l'AI Lab (arXiv 2609.00006).
- Version 2.0.0 (`pyproject.toml`, `__version__`, `cli.VERSION`, `uv.lock`) et `CHANGELOG.md` créé.

## Tests

`tests/test_compat.py` couvre le repli des variables, l'avertissement unique, la migration (copie, seconde copie sans effet, copie interrompue, dossier absent, surcharge) et `data_dir()` sur la plateforme courante. `tests/test_installers.py` couvre le repli dans `install.sh` et `install.ps1`.

## Reports

- Captures non régénérées (il faut une session E2E de plus de 15 min et le modèle local) : `tools/e2e/screenshots/*.jpg`, `docs/assets/atelier.jpg`, `docs/assets/harness-lab-demo.gif`, `docs/assets/harness-lab-demo.mp4`.
- Application OAuth GitHub « WaveStack » (`mcp/github_auth.py`, `CLIENT_ID`) : à renommer par Anaël dans les réglages GitHub.
- Pictogramme : pas de valeur de repli `#hex` dans les `var()`, car `test_static_files_write_no_color_outside_the_tokens` interdit tout hexadécimal hors de `tokens.css`, et toutes les pages chargent `tokens.css` en premier.
- Variables internes des tests et des E2E (`HARNESS_LAB_TEST_*`, `HARNESS_LAB_E2E_*`) : renommées sans repli.
- Mentions historiques de « violet » et d'Aptos dans les revues et les memlogs datés de `_bmad-output` : laissées telles quelles, car ce sont des archives.
