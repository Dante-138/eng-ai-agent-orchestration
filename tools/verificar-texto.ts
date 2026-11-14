// Portão do texto versionado: tudo que está no repositório é público.
//
// Uso:
//   node tools/verificar-texto.ts             confere todos os arquivos versionados
//   node tools/verificar-texto.ts <arquivo>   confere só os arquivos dados
//
// Regras:
// 1. Sem travessão nem meia-risca (use hífen, vírgula, dois-pontos ou parêntese)
// 2. Sem emoji
// 3. Sem endereço de e-mail (exceto nos testes, que precisam de exemplos)
// 4. Sem termo da lista proibida, a mesma do portão de commits
//    (secret TERMOS_PROIBIDOS no CI, arquivo local no PC)
// 5. Link relativo em Markdown aponta para um arquivo que existe

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, normalize } from 'node:path';
import { pathToFileURL } from 'node:url';
import { contemTermo, normalizar, termosConfigurados } from './verificar-commits.ts';

const EXTENSOES = ['.md', '.ts', '.mjs', '.js', '.json', '.yml', '.yaml', '.sh', '.ps1', '.txt'];
const IGNORADOS = new Set(['package-lock.json']);
const TRAVESSAO = /[\u2013\u2014]/u;
const EMOJI = /\p{Emoji_Presentation}|\p{Extended_Pictographic}\uFE0F/u;
const EMAIL = /[\p{L}\p{N}._%+-]+@[\p{L}\p{N}-]+(\.[\p{L}\p{N}-]+)*\.\p{L}{2,}/u;
const LINK = /\]\(([^)\s]+)\)/g;

export interface Problema {
  linha: number;
  motivo: string;
}

/** Tira blocos de código cercados e trechos em crase: o que está ali não é link. */
export function semCodigo(markdown: string): string {
  let dentroDeBloco = false;
  return markdown
    .split('\n')
    .map((linha) => {
      if (linha.trimStart().startsWith('```')) {
        dentroDeBloco = !dentroDeBloco;
        return '';
      }
      return dentroDeBloco ? '' : linha.replace(/`[^`]*`/g, '');
    })
    .join('\n');
}

/** Destinos de link relativo (sem âncora) de um Markdown. */
export function linksRelativos(markdown: string): { linha: number; destino: string }[] {
  const links: { linha: number; destino: string }[] = [];
  semCodigo(markdown)
    .split('\n')
    .forEach((texto, indice) => {
      for (const [, alvo = ''] of texto.matchAll(LINK)) {
        if (/^([a-z]+:|#|<)/i.test(alvo)) continue;
        const destino = alvo.split('#', 1)[0] ?? '';
        if (destino) links.push({ linha: indice + 1, destino });
      }
    });
  return links;
}

/**
 * Problemas de um arquivo. "existe" responde se um caminho (relativo à raiz)
 * existe; é parâmetro para o teste não depender do disco.
 */
export function problemasDoArquivo(
  caminho: string,
  conteudo: string,
  termos: readonly string[] = [],
  existe: (caminho: string) => boolean = existsSync,
): Problema[] {
  const problemas: Problema[] = [];
  const ehTeste = caminho.startsWith('tests/');
  conteudo.split('\n').forEach((texto, indice) => {
    const linha = indice + 1;
    if (TRAVESSAO.test(texto)) problemas.push({ linha, motivo: 'travessão ou meia-risca' });
    if (EMOJI.test(texto)) problemas.push({ linha, motivo: 'emoji' });
    if (!ehTeste && EMAIL.test(texto)) problemas.push({ linha, motivo: 'endereço de e-mail' });
    const normalizado = normalizar(texto);
    // O aviso diz só o número do termo: o log do CI é público.
    termos.forEach((termo, posicao) => {
      if (contemTermo(normalizado, termo)) problemas.push({ linha, motivo: `termo proibido nº ${posicao + 1}` });
    });
  });
  if (caminho.endsWith('.md')) {
    for (const { linha, destino } of linksRelativos(conteudo)) {
      const alvo = normalize(join(dirname(caminho), destino)).replaceAll('\\', '/');
      if (!existe(alvo)) problemas.push({ linha, motivo: `link para "${destino}", que não existe` });
    }
  }
  return problemas;
}

/** O arquivo entra na conferência? */
export function conferir(caminho: string): boolean {
  const nome = caminho.split('/').pop() ?? '';
  return !IGNORADOS.has(nome) && EXTENSOES.some((extensao) => nome.endsWith(extensao));
}

function arquivosVersionados(): string[] {
  const saida = execFileSync('git', ['ls-files', '-z'], { encoding: 'utf8' });
  return saida.split('\0').filter(Boolean);
}

function principal(argumentos: string[]): number {
  const termos = termosConfigurados();
  const arquivos = (argumentos.length > 0 ? argumentos : arquivosVersionados()).filter(conferir);
  let total = 0;
  for (const arquivo of arquivos) {
    for (const { linha, motivo } of problemasDoArquivo(arquivo, readFileSync(arquivo, 'utf8'), termos)) {
      console.error(`REPROVADO  ${arquivo}:${linha}  ${motivo}`);
      total += 1;
    }
  }
  console.log(`${arquivos.length} arquivo(s) conferido(s), ${total} problema(s).`);
  return total > 0 ? 1 : 0;
}

// Executado direto pela linha de comando (e não importado por um teste).
if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  process.exitCode = principal(process.argv.slice(2));
}
