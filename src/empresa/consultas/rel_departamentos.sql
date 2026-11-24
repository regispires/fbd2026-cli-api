-- consulta de negócio 1: folha, média e projetos por departamento (visão)
SELECT dnumero, dnome, qtd_func, folha, media, qtd_proj
  FROM vw_resumo_departamento
 ORDER BY dnumero
