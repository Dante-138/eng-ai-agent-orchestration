// Confere os workflows do GitHub Actions com o actionlint (sintaxe, expressões,
// tipos dos inputs e, pelo shellcheck que vem na imagem, os scripts dos "run").
// Roda igual no CI e no PC; no PC precisa do Docker Desktop aberto.
//
// A imagem é fixada pelo digest: o mesmo binário sempre.

import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const IMAGEM = 'rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667';

const raiz = fileURLToPath(new URL('..', import.meta.url));
const resultado = spawnSync('docker', ['run', '--rm', '-v', `${raiz}:/repo`, '-w', '/repo', IMAGEM, '-color'], {
  stdio: 'inherit',
});

process.exitCode = resultado.status ?? 1;
