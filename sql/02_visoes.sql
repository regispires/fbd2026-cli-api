-- Visões consultadas pela aplicação

CREATE OR REPLACE VIEW vw_funcionario_depto AS
SELECT f.cpf, f.pnome, f.unome,
       concat_ws(' ', f.pnome, f.minicial,
                 f.unome) AS nome,
       f.salario, f.datanasc,
       d.dnumero, d.dnome,
       s.pnome AS supervisor
  FROM funcionario f
  JOIN departamento d ON d.dnumero = f.dnr
  LEFT JOIN funcionario s
         ON s.cpf = f.cpf_supervisor;

CREATE OR REPLACE VIEW vw_resumo_departamento AS
SELECT d.dnumero, d.dnome,
       count(f.cpf)                AS qtd_func,
       coalesce(sum(f.salario), 0) AS folha,
       round(avg(f.salario), 2)    AS media,
       (SELECT count(*) FROM projeto p
         WHERE p.dnum = d.dnumero) AS qtd_proj
  FROM departamento d
  LEFT JOIN funcionario f ON f.dnr = d.dnumero
 GROUP BY d.dnumero;
