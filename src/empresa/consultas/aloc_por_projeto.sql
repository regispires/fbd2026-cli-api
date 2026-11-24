SELECT f.cpf,
       concat_ws(' ', f.pnome, f.minicial, f.unome) AS nome,
       p.projnumero, p.projnome, t.horas
  FROM trabalha_em t
  JOIN funcionario f ON f.cpf = t.fcpf
  JOIN projeto p ON p.projnumero = t.pnr
 WHERE t.pnr = %(projnumero)s
 ORDER BY nome
