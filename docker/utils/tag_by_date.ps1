docker tag makerspet/oomwoo:humble "$((get-date).toString('makerspet/oomwoo:\hu\mble-MM-dd-yyyy'))"
docker push "$((get-date).toString('makerspet/oomwoo:\hu\mble-MM-dd-yyyy'))"
docker tag makerspet/oomwoo:iron "$((get-date).toString('makerspet/oomwoo:iron-MM-dd-yyyy'))"
docker push "$((get-date).toString('makerspet/oomwoo:iron-MM-dd-yyyy'))"
