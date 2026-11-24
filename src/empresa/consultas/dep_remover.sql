DELETE FROM departamento
 WHERE dnumero = %(dnumero)s
RETURNING dnumero
