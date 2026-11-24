-- consulta de negócio 4: cadeia de supervisão a partir de um funcionário
WITH RECURSIVE sub AS (
    SELECT cpf, pnome, unome, cpf_supervisor, 0 AS nivel
      FROM funcionario WHERE cpf = %(raiz)s
    UNION ALL
    SELECT f.cpf, f.pnome, f.unome, f.cpf_supervisor, s.nivel + 1
      FROM funcionario f JOIN sub s ON f.cpf_supervisor = s.cpf
) CYCLE cpf SET em_ciclo USING caminho
SELECT cpf, pnome || ' ' || unome AS nome, cpf_supervisor
  FROM sub
 WHERE NOT em_ciclo
 ORDER BY nivel, pnome
