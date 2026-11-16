#!/usr/bin/env bash
# Liga no GitHub as proteções que o portão de qualidade pressupõe.
# Rode uma vez por repositório, depois do primeiro push da main, com o gh logado
# numa conta com permissão de admin no repositório.
#
# Uso: bash tools/configurar-repo.sh dono/repositorio
#
# O que faz (tudo idempotente, pode rodar de novo):
#   1. Merge só por squash, com título e descrição do PR como mensagem (o texto
#      revisado, não a lista de commits do branch); apaga o branch depois.
#   2. Token dos workflows só leitura por padrão; Actions não aprova PR.
#   3. Secret scanning com push protection, alertas e correções do Dependabot.
#   4. Protege a main: PR obrigatório, checks Texto do PR e Gate verdes,
#      branch atualizado com a main, histórico linear, conversas resolvidas,
#      sem force push, sem apagar, e tudo isso vale também para o admin.
#
# No plano gratuito do GitHub, a proteção de branch e a push protection só
# funcionam em repositório público.

set -euo pipefail

REPO="${1:?uso: bash tools/configurar-repo.sh dono/repositorio}"
CHECKS=("Texto do PR" "Gate")

echo "1/4 Merge só por squash"
gh api -X PATCH "repos/$REPO" --silent \
  -F allow_squash_merge=true \
  -F allow_merge_commit=false \
  -F allow_rebase_merge=false \
  -F allow_auto_merge=false \
  -F delete_branch_on_merge=true \
  -f squash_merge_commit_title=PR_TITLE \
  -f squash_merge_commit_message=PR_BODY

echo "2/4 Token dos workflows só leitura"
gh api -X PUT "repos/$REPO/actions/permissions/workflow" --silent \
  -f default_workflow_permissions=read \
  -F can_approve_pull_request_reviews=false

echo "3/4 Secret scanning, push protection e Dependabot"
gh api -X PATCH "repos/$REPO" --silent --input - <<'JSON'
{
  "security_and_analysis": {
    "secret_scanning": { "status": "enabled" },
    "secret_scanning_push_protection": { "status": "enabled" }
  }
}
JSON
gh api -X PUT "repos/$REPO/vulnerability-alerts" --silent
gh api -X PUT "repos/$REPO/automated-security-fixes" --silent

echo "4/4 Proteção da main (checks: ${CHECKS[*]})"
contextos=$(printf '"%s",' "${CHECKS[@]}")
gh api -X PUT "repos/$REPO/branches/main/protection" --silent --input - <<JSON
{
  "required_status_checks": { "strict": true, "contexts": [${contextos%,}] },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
JSON

echo "Pronto. Conferir em https://github.com/$REPO/settings/branches"
