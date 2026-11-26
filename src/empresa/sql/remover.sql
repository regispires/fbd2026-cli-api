-- Remove as visões e as tabelas do esquema EMPRESA.
-- Usado por `empresa banco criar --recriar`, na mesma transação que recria o
-- esquema: se a recriação falhar, nada é removido.

DROP VIEW IF EXISTS vw_resumo_departamento, vw_funcionario_depto;

DROP TABLE IF EXISTS dependente, trabalha_em, localizacoes_dep, projeto,
  funcionario, departamento CASCADE;
