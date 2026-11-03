# Changelog

## 2.0.0 — 2026-11-03

Changement majeur : le projet WaveStack devient **HarnessLab**, une version publique générique.

- **Nouveau nom** : dépôt `harness-lab` (https://github.com/Aliquanto3/harness-lab), nom affiché
  HarnessLab, paquet Python `harness_lab` (ancien `wavestack`), commande `uv run harness-lab`
  (l'ancienne commande `wavestack` n'existe plus), configuration `harness-lab.toml` (ancien
  `wavestack.toml`).
- **Nouvelle charte** : palette générique (bleu pétrole, orange brûlé), mêmes noms de jetons,
  nouveau pictogramme et logotype texte, nouveau favicon. Nouveau jeton `on-status` : texte sur
  les aplats d'état (succès, erreur, accent), blanc en clair et encre en sombre.
- **Variables d'environnement** : préfixe `HARNESS_LAB_` (ancien `WAVESTACK_`). Les anciens noms
  restent lus en repli, avec un avertissement de dépréciation : `WAVESTACK_DATA_DIR` par
  l'application, les variables des installeurs (`WAVESTACK_INSTALL_DIR`, `WAVESTACK_MODELS`…) et
  `WAVESTACK_LLAMA_SERVER` du banc. Les variables internes des tests et des E2E
  (`HARNESS_LAB_TEST_*`, `HARNESS_LAB_E2E_*`) sont seulement renommées.
- **Dossier de données** : `%LOCALAPPDATA%\HarnessLab` sous Windows, `~/.local/share/harness-lab`
  ailleurs. Au premier lancement (ou à la première installation), l'ancien dossier
  (`%LOCALAPPDATA%\WaveStack`, `~/.local/share/wavestack`) est copié vers le nouveau si celui-ci
  n'existe pas encore ; l'ancien n'est jamais supprimé.
- **Anciens liens** : GitHub redirige `Aliquanto3/wavestack` vers `Aliquanto3/harness-lab`.
  Mettez à jour vos clones : `git remote set-url origin https://github.com/Aliquanto3/harness-lab.git`.
  Les réglages d'affichage gardés par le navigateur (thème, volets) repartent de leurs valeurs
  par défaut : leurs clés passent de `wavestack.*` à `harness_lab.*`.
