SELECT f.id AS funcionario_id, f.cpf,
       concat_ws(' ', f.pnome, f.minicial, f.unome) AS nome,
       p.id AS projeto_id, p.projnome, t.horas
  FROM trabalha_em t
  JOIN funcionario f ON f.id = t.funcionario_id
  JOIN projeto p ON p.id = t.projeto_id
 WHERE t.projeto_id = %(projeto_id)s
 ORDER BY nome
