SELECT IFNULL(sum(sec), 0) AS total 
FROM distancements 
WHERE no = 3 
AND dist <= 5
AND savetime >= DATETIME('now','localtime', '-' || 10 || ' seconds')
