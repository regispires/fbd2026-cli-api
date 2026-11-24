-- consulta de negócio 3 (divisão relacional): funcionários alocados em
-- todos os projetos do próprio departamento
SELECT f.cpf,
       concat_ws(' ', f.pnome, f.minicial, f.unome) AS nome,
       d.dnome
  FROM funcionario f
  JOIN departamento d ON d.dnumero = f.dnr
 WHERE EXISTS (SELECT 1 FROM projeto p
                WHERE p.dnum = f.dnr)
   AND NOT EXISTS (
       SELECT 1 FROM projeto p
        WHERE p.dnum = f.dnr
          AND NOT EXISTS (
              SELECT 1 FROM trabalha_em t
               WHERE t.fcpf = f.cpf
                 AND t.pnr = p.projnumero))
 ORDER BY d.dnome, nome
