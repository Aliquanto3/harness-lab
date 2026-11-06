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

## Revue

### Passe 1 (2026-11-03, SHA revu 10abd831)

- Important, medium, second avis 1 : `compat.getenv` émettait un `DeprecationWarning`, masqué par défaut. Corrigé : `FutureWarning`, test en sous-processus sans filtre.
- Important, medium, second avis 2 : l'E2E attendait `--color-on-vivid` sur le rouge, le CSS pose `--color-on-status`. Corrigé (trois contrôles et l'aide `_on_status_both_themes`), E2E non relancé.
- Important, medium, second avis 3 : DESIGN.md rattachait le texte sur rouge et sur les pastilles d'état à `on-vivid`. Corrigé (liaisons `confirmed-foreground`, `overflow-foreground`, `badge-foreground`, prose et tableau « à faire / à éviter »). Ligne 514 (`hosting-tag-network`, fond jaune) laissée en `on-vivid` : c'est un fond vif.
- Important, medium, second avis 4 : cahiers de recette en accent violet (#4B2BD6, sombre #A594FF). Corrigé : primaire #0B6B78 et #4FC1CF.
- Important, medium, second avis 5 : un échec de copie de l'ancien dossier bloquait le démarrage, et le staging `.migration` était partagé. Corrigé : staging `.migration-<pid>`, `OSError` attrapée, `RuntimeWarning` une fois par processus, pas de nouvel essai, ancien dossier intact ; lancement concurrent qui a migré le premier toléré. Trois tests (verrou, disque plein via `data_dir`, concurrence).
- Nit, low, second avis 6 : liens vers la forge supprimée. Corrigé (source retirée de SPEC v2, déclencheur neutre).
- Nit, low, second avis 7 : pictogrammes MCP maison en #33257A. Corrigé : encre #141A1F pour `_default`, `local`, `datagouv` et `mslearn`, qui sont des pictogrammes maison, pas des logos d'éditeurs.
- Nit, low, second avis 8 : `.bar-log-count` en `surface-raised` sur le rouge. Corrigé : `--color-on-status`.
- Nit, low, second avis 9 : test de migration des installeurs. Reporté : `test_installers.py` ne lance les installeurs qu'en `-DryRun` ou dans la branche idempotente, et la migration est sautée en `-DryRun`. À vérifier à la main : lancer `install.ps1` avec un `%LOCALAPPDATA%\WaveStack` existant et sans `HarnessLab`.
- Nit, low, second avis 10 : recopie après suppression du nouveau dossier. Rejeté : conforme à la règle (copie au premier lancement, jamais de suppression).
- Nit, low, second avis 11 : « PC d'un collègue » dans deux archives de nuit. Corrigé : « un autre PC ».
- Important, low, reviewer : `install.ps1` copiait l'ancien dossier par défaut vers un `HARNESS_LAB_DATA_DIR` choisi, contrairement à l'application et à `install.sh`. Corrigé : copie vers le dossier par défaut seulement.
- Complexité : 0 constat (`data_dir()` ne teste que l'existence du nouveau dossier à chaque appel).

### Passe 2 (2026-11-06, SHA revu 58be3f51, story 3.1, delta 3b551cc..58be3f5)
- Aucun constat Important. Test anti-aplat : ne rejette pas `primary-soft` (assertion négative ajoutée par l'implémenteur) ; mutation manuelle (repli `var(--color-primary)` remis sur `.brick-toggle:checked`) : `test_le_bleu_n_est_jamais_un_aplat_de_bouton` échoue, puis restauré.
- `tools/demo/compose.py` : Python valide (lu en UTF-8), couleurs v2.1. CHANGELOG sans valeur hex de l'ancienne charte. Aucune référence restante aux PNG et à `pictogramme.svg` supprimés (hors l'assertion d'absence du test).
- Complexité : 0 constat. ruff et `tests/test_web_tokens.py` (28) verts.
