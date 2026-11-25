-- consulta de negócio 2: ranking salarial por departamento (função de janela)
SELECT dnome, nome, salario,
       dense_rank() OVER w AS posicao,
       round(salario - avg(salario) OVER
             (PARTITION BY departamento_id), 2) AS dif_media
  FROM vw_funcionario_depto
 WHERE departamento_id = ANY(%(deps)s)
WINDOW w AS (PARTITION BY departamento_id
             ORDER BY salario DESC)
 ORDER BY dnome, posicao, nome
