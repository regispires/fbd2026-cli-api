-- consulta de negócio 5: projetos com equipe pequena (até N funcionários)
-- O LEFT JOIN mantém os projetos sem alocação; count(t.funcionario_id)
-- conta só as linhas com par, então esses projetos aparecem com 0.
-- O HAVING filtra os grupos depois da agregação; o WHERE não poderia,
-- porque roda antes do GROUP BY e não enxerga o count.
SELECT p.id, p.projnome, d.dnome,
       count(t.funcionario_id)   AS qtd_func,
       coalesce(sum(t.horas), 0) AS total_horas
  FROM projeto p
  JOIN departamento d ON d.id = p.departamento_id
  LEFT JOIN trabalha_em t ON t.projeto_id = p.id
 GROUP BY p.id, d.dnome
HAVING count(t.funcionario_id) <= %(max_func)s
 ORDER BY qtd_func, p.projnome
