-- consulta de negócio 6: funcionários com pelo menos N dependentes
-- Com N = 0 aparecem todos, inclusive os sem dependentes, o que só é possível
-- com o LEFT JOIN. count(*) daria 1 para quem não tem dependentes, porque a
-- linha do funcionário existe; count(d.id) ignora o NULL e dá 0.
SELECT f.id, f.cpf,
       concat_ws(' ', f.pnome, f.minicial, f.unome) AS nome,
       count(d.id) AS qtd_dependentes
  FROM funcionario f
  LEFT JOIN dependente d ON d.funcionario_id = f.id
 GROUP BY f.id
HAVING count(d.id) >= %(min_dep)s
 ORDER BY qtd_dependentes DESC, nome
