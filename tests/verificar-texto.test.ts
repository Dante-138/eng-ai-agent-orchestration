import { describe, expect, test } from 'vitest';
import { conferir, linksRelativos, problemasDoArquivo, semCodigo } from '../tools/verificar-texto.ts';

const nenhumArquivo = (_caminho: string) => false;
const motivos = (caminho: string, conteudo: string, termos: string[] = [], existe = nenhumArquivo) =>
  problemasDoArquivo(caminho, conteudo, termos, existe).map(({ linha, motivo }) => `${linha}: ${motivo}`);

describe('portão do texto versionado', () => {
  test('aceita texto comum', () => {
    expect(motivos('guias/a.md', '# Título\n\nTexto com hífen - e vírgula, (parêntese).\n')).toEqual([]);
  });

  test.each(['\u2014', '\u2013'])('acha travessão e meia-risca (%j) com a linha', (traco) => {
    expect(motivos('a.md', `ok\nantes ${traco} depois`)).toEqual(['2: travessão ou meia-risca']);
  });

  test('acha emoji', () => {
    expect(motivos('a.md', 'pronto \u{1F680}')).toEqual(['1: emoji']);
  });

  test('acha emoji de texto com seletor de apresentação', () => {
    expect(motivos('a.md', 'coração \u2764\uFE0F')).toEqual(['1: emoji']);
  });

  test.each(['\u00A9 2026', 'marca\u2122', 'ida \u2194 volta'])(
    'não confunde símbolo de texto com emoji: %j',
    (texto) => {
      expect(motivos('a.md', texto)).toEqual([]);
    },
  );

  test('acha e-mail fora dos testes e deixa os testes usarem exemplo', () => {
    const texto = `fale com fulano${'@'}exemplo.com`;
    expect(motivos('guias/a.md', texto)).toEqual(['1: endereço de e-mail']);
    expect(motivos('tests/a.test.ts', texto)).toEqual([]);
  });

  test('acha termo proibido sem repetir o termo no aviso', () => {
    expect(motivos('a.md', 'linha\nfeito para a ACME', ['Acme'])).toEqual(['2: termo proibido nº 1']);
  });

  test('link relativo quebrado reprova; o que existe passa', () => {
    const md = '[ok](b.md) e [quebrado](../nao/existe.md#secao)';
    expect(motivos('guias/a.md', md, [], (caminho) => caminho === 'guias/b.md')).toEqual([
      '1: link para "../nao/existe.md", que não existe',
    ]);
  });

  test('link de fora, âncora e código não são conferidos', () => {
    const md = [
      '[site](https://exemplo.org) [ancora](#topo) [modelo](<algo>)',
      '`[em crase](x.md)`',
      '```',
      '[no bloco](y.md)',
      '```',
    ].join('\n');
    expect(linksRelativos(md)).toEqual([]);
    expect(semCodigo('a `b` c')).toBe('a  c');
  });

  test('confere só arquivo de texto e pula o lockfile', () => {
    expect(conferir('guias/a.md')).toBe(true);
    expect(conferir('tools/x.ts')).toBe(true);
    expect(conferir('package-lock.json')).toBe(false);
    expect(conferir('imagem.png')).toBe(false);
  });
});
