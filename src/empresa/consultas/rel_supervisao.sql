-- consulta de negócio 4: cadeia de supervisão a partir de um funcionário
WITH RECURSIVE sub AS (
    SELECT id, cpf, pnome, unome, supervisor_id, 0 AS nivel
      FROM funcionario WHERE id = %(raiz)s
    UNION ALL
    SELECT f.id, f.cpf, f.pnome, f.unome, f.supervisor_id, s.nivel + 1
      FROM funcionario f JOIN sub s ON f.supervisor_id = s.id
) CYCLE id SET em_ciclo USING caminho
SELECT id, cpf, pnome || ' ' || unome AS nome, supervisor_id
  FROM sub
 WHERE NOT em_ciclo
 ORDER BY nivel, pnome
