import { describe, expect, test } from 'vitest';
import {
  ehDependabot,
  lerTermos,
  limparMensagemDoEditor,
  normalizar,
  problemaDoDestino,
  problemasDaMensagem,
  problemasDoAssunto,
  problemasDoTexto,
  TAMANHO_MAXIMO,
} from '../tools/verificar-commits.ts';

describe('portão de commits', () => {
  test.each(['feat: add a deadline field', 'fix(nucleo): reject 2026-02-30', 'refactor!: drop the old format'])(
    'aceita %j',
    (assunto) => {
      expect(problemasDoAssunto(assunto)).toEqual([]);
    },
  );

  test.each([
    ['Add a field', 'fora do padrão'],
    ['feat:missing space', 'fora do padrão'],
    ['feature: wrong type', 'fora do padrão'],
    ['feat(Escopo): uppercase scope', 'fora do padrão'],
    ['fix: ends with a period.', 'ponto final'],
  ])('recusa %j', (assunto, motivo) => {
    expect(problemasDoAssunto(assunto).join(' ')).toContain(motivo);
  });

  // Caso real: um assunto com 74 caracteres passou no check local (que não
  // conferia commits) e só reprovou no CI.
  test('recusa assunto acima do limite e aceita no limite', () => {
    const prefixo = 'feat: ';
    const noLimite = prefixo + 'x'.repeat(TAMANHO_MAXIMO - prefixo.length);
    expect(problemasDoAssunto(noLimite)).toEqual([]);
    expect(problemasDoAssunto(`${noLimite}y`)).toEqual([`tem ${TAMANHO_MAXIMO + 1} caracteres (máximo 72)`]);
  });

  test.each([
    'feat: x\n\nCo-Authored-By: Alguém <a@b.c>',
    'feat: x\n\nGenerated with some tool',
    'feat: x\n\n\u{1F916} assinatura',
    'feat: x\n\nSigned-off-by: Alguém <a@b.c>',
  ])('recusa coautoria ou "gerado por": %j', (mensagem) => {
    expect(problemasDaMensagem(mensagem)).toEqual(['contém linha de coautoria ou de "gerado por"']);
  });

  test('aceita corpo comum', () => {
    expect(problemasDaMensagem('fix: handle leap years\n\nThe old check missed 2028-02-29.')).toEqual([]);
  });

  test('PR só vai para a main', () => {
    expect(problemaDoDestino('main')).toBeNull();
    expect(problemaDoDestino('feat/base')).toContain('pilha de PRs');
  });
});

describe('texto que vai para o histórico', () => {
  const termos = lerTermos('# nomes que nunca entram\nJosé da Silva, Acme\n\nprojeto-x # cliente\n');

  test('lê a lista de termos com vírgula, linha e comentário', () => {
    expect(termos).toEqual(['José da Silva', 'Acme', 'projeto-x']);
  });

  test('normaliza acento e maiúscula', () => {
    expect(normalizar('JOSÉ Ação')).toBe('jose acao');
  });

  // Caso real: no Git Bash, a classe [ií] não casa o "í" de dois bytes e a busca
  // deu falso "nada". Aqui a comparação é feita depois de tirar o acento.
  test.each(['Revisado com o jose da silva', 'ver ACME amanhã', 'Pedido do José da Silva'])(
    'acha termo proibido em %j sem repetir o termo no aviso',
    (texto) => {
      const problemas = problemasDoTexto(texto, termos);
      expect(problemas).toHaveLength(1);
      expect(problemas[0]).toMatch(/^contém o termo proibido nº \d da lista$/);
    },
  );

  test('não acusa termo dentro de outra palavra', () => {
    expect(problemasDoTexto('acmezinho e projeto-xy', termos)).toEqual([]);
  });

  test.each(['fale com fulano@exemplo.com', 'contato: joão.silva@empresa.com.br'])('acha e-mail em %j', (texto) => {
    expect(problemasDoTexto(texto)).toEqual(['contém endereço de e-mail']);
  });

  test('aceita texto comum de PR', () => {
    expect(problemasDoTexto('## O que muda\n\nAdiciona o campo de prazo. Ver @arquivo e 2026-11-14.')).toEqual([]);
  });

  test('a mensagem junta as regras do assunto e do texto', () => {
    expect(problemasDaMensagem('fix: thanks Acme.', termos)).toEqual([
      'termina com ponto final',
      'contém o termo proibido nº 2 da lista',
    ]);
  });

  test('limpa comentários e o diff do editor, como o git faz', () => {
    const bruta =
      'feat: add x\n\nbody\n# comentário\n# ------------------------ >8 ------------------------\ndiff --git a b\n';
    expect(limparMensagemDoEditor(bruta)).toBe('feat: add x\n\nbody');
  });
});

describe('exceção do Dependabot', () => {
  const ROBO = 'dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>';
  const ASSINATURA = 'Signed-off-by: dependabot[bot] <support@github.com>';
  const mensagem = (...corpo: string[]) => ['build: bump the npm group with 2 updates', '', ...corpo].join('\n');

  test('aceita a assinatura dele só em commit dele', () => {
    expect(ehDependabot(ROBO)).toBe(true);
    expect(problemasDaMensagem(mensagem('Bumps eslint.', '', ASSINATURA), [], ROBO)).toEqual([]);
  });

  test('a mesma linha vinda de uma pessoa, ou sem autor, reprova', () => {
    expect(problemasDaMensagem(mensagem(ASSINATURA), [], 'Fulano <fulano@exemplo.com>')).toHaveLength(2);
    expect(problemasDaMensagem(mensagem(ASSINATURA))).toHaveLength(2);
  });

  test('o nome do robô com outro e-mail não é o robô', () => {
    expect(ehDependabot('dependabot[bot] <alguem@exemplo.com>')).toBe(false);
    expect(problemasDaMensagem(mensagem(ASSINATURA), [], 'dependabot[bot] <alguem@exemplo.com>')).toHaveLength(2);
  });

  test.each([
    'Co-authored-by: Alguém <a@b.cc>',
    'Signed-off-by: Alguém <a@b.cc>',
    'Generated with some tool',
    `${ASSINATURA} e mais texto na mesma linha`,
  ])('coautoria, assinatura de outra pessoa e "gerado por" reprovam também para ele: %j', (linha) => {
    expect(problemasDaMensagem(mensagem(ASSINATURA, linha), [], ROBO)).toContain(
      'contém linha de coautoria ou de "gerado por"',
    );
  });
});
