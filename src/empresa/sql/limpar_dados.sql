-- Apaga todos os dados e reinicia as sequências IDENTITY.
-- Usado por `empresa banco povoar --limpar`, na mesma transação que carrega os
-- dados de exemplo: se a carga falhar, os dados anteriores continuam lá.

TRUNCATE dependente, trabalha_em, localizacoes_dep, projeto,
  departamento, funcionario RESTART IDENTITY CASCADE;
