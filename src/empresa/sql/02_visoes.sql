-- Visões consultadas pela aplicação

CREATE OR REPLACE VIEW vw_funcionario_depto AS
SELECT f.id, f.cpf, f.pnome, f.unome,
       concat_ws(' ', f.pnome, f.minicial,
                 f.unome) AS nome,
       f.salario, f.datanasc,
       d.id AS departamento_id, d.dnome,
       s.pnome AS supervisor
  FROM funcionario f
  JOIN departamento d ON d.id = f.departamento_id
  LEFT JOIN funcionario s
         ON s.id = f.supervisor_id;

CREATE OR REPLACE VIEW vw_resumo_departamento AS
SELECT d.id, d.dnome,
       count(f.id)                 AS qtd_func,
       coalesce(sum(f.salario), 0) AS folha,
       round(avg(f.salario), 2)    AS media,
       (SELECT count(*) FROM projeto p
         WHERE p.departamento_id = d.id) AS qtd_proj
  FROM departamento d
  LEFT JOIN funcionario f ON f.departamento_id = d.id
 GROUP BY d.id;
