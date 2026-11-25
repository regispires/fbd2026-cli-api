-- consulta de negócio 3 (divisão relacional): funcionários alocados em
-- todos os projetos do próprio departamento
SELECT f.id, f.cpf,
       concat_ws(' ', f.pnome, f.minicial, f.unome) AS nome,
       d.dnome
  FROM funcionario f
  JOIN departamento d ON d.id = f.departamento_id
 WHERE EXISTS (SELECT 1 FROM projeto p
                WHERE p.departamento_id = f.departamento_id)
   AND NOT EXISTS (
       SELECT 1 FROM projeto p
        WHERE p.departamento_id = f.departamento_id
          AND NOT EXISTS (
              SELECT 1 FROM trabalha_em t
               WHERE t.funcionario_id = f.id
                 AND t.projeto_id = p.id))
 ORDER BY d.dnome, nome
