-- consulta de negócio 2: ranking salarial por departamento (função de janela)
SELECT dnome, nome, salario,
       dense_rank() OVER w AS posicao,
       round(salario - avg(salario) OVER
             (PARTITION BY dnumero), 2) AS dif_media
  FROM vw_funcionario_depto
 WHERE dnumero = ANY(%(deps)s)
WINDOW w AS (PARTITION BY dnumero
             ORDER BY salario DESC)
 ORDER BY dnome, posicao, nome
