import urllib
import urllib2
import json


class Client(object):
    """Client wrapper for PivotalTracker API"""

    def __init__(self, token, secure=True,):
        self.__token = token
        protocol = "https" if secure else "http"
        self.__base_url = "%(protocol)s://www.pivotaltracker.com/services/v5/" % dict(protocol=protocol)

    def get_project(self, project_id):
        """gets a project from the tracker"""
        return self.__remote_http_get("projects/%s" % project_id)
        
    def get_all_projects(self):
        """gets all projects for this user"""
        return self.__remote_http_get("projects")
    
    def get_story(self, project_id, story_id):
        """gets an individual story"""
        return self.__remote_http_get("projects/%s/stories/%s" % (project_id, story_id))
    
    def get_stories(self, project_id, query=None, limit=None, offset=None, fields=None):
        """gets stories from a project.  These stories can be filtered via 'query', and
        paginated via 'limit' and 'offset'"""
        params = {}
        if query:
            params["filter"] = query
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        if fields:
            params['fields'] = fields
        if params:
            # we have parameters to send
            encoded_params = urllib.urlencode(params)
            return self.__remote_http_get("projects/%s/stories?%s" % (project_id, encoded_params))
        else:
            # no arguments, get all stories
            return self.__remote_http_get("projects/%s/stories" % project_id)
        
    def get_iterations(self, project_id, limit=None, offset=None):
        """gets iterations from a project.  These iterations can be paginated via 'limit' and 'offset'"""
        return self.__iterations_request_helper(sub_url="iterations", project_id=project_id, limit=limit, offset=offset)
        
    def get_done_iterations(self, project_id, limit=None, offset=None):
        """gets all done iterations from a project.  These iterations can be paginated via 'limit' and 'offset'"""
        if offset is not None:
            offset = -1*offset
        return self.__iterations_request_helper(sub_url="iterations/done", project_id=project_id, limit=limit, offset=offset)
        
    def get_current_iterations(self, project_id, limit=None, offset=None):
        """gets current iteration from a project.  These iterations can be paginated via 'limit' and 'offset'"""
        return self.__iterations_request_helper(sub_url="iterations/current", project_id=project_id, limit=limit, offset=offset)
        
    def get_backlog_iterations(self, project_id, limit=None, offset=None):
        """gets backlog from a project.  These iterations can be paginated via 'limit' and 'offset'"""
        return self.__iterations_request_helper(sub_url="iterations/backlog", project_id=project_id, limit=limit, offset=offset)


    def __get_story_json(project_id, name, description, requested_by, story_type, estimate, current_state, labels):
        return {'name': name,
                'description': description,
                'requested_by': requested_by,
                'story_type': story_type,
                'estimate': estimate,
                'current_state': current_state,
                'labels': labels}

    def add_story(self, project_id, name, description, story_type, requested_by=None, estimate=None, current_state=None, labels=None):
        """adds a story to a project"""
        data = self.__get_story_dict(project_id, name, description, requested_by, story_type, estimate, current_state, labels)
        return self.__remote_http_post("projects/%s/stories" % project_id, data=data)
    
    def update_story(self, project_id, story_id, name=None, description=None, requested_by=None, story_type=None, estimate=None, current_state=None, labels=None):
        """updates a story in a project"""
        data = self.__get_story_dict(project_id, name, description, requested_by, story_type, estimate, current_state, labels)
        return self.__remote_http_put("projects/%s/stories/%s" % (project_id, story_id), data=data)
    
    def delete_story(self, project_id, story_id):
        """deletes a story in a project"""
        return self.__remote_http_delete("projects/%s/stories/%s" % (project_id, story_id))
    
    def add_comment(self, project_id, story_id, text, author=None):
        """adds a comment to a story in a project"""
        #todo: author

        data = {"text": text}
        return self.__remote_http_post("projects/%s/stories/%s/comments" % (project_id, story_id), data=data)
    
    def deliver_all_finished_stories(self, project_id):
        """delivers all finished stories in a project.  This is perfect for automated
        deployments to a staging server, indicating that the code has been deployed
        for live testing."""
        return self.__remote_http_put("projects/%s/stories/deliver_all_finished" % project_id)

    def __iterations_request_helper(self, sub_url, project_id, limit, offset):
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if params:
            # we have parameters to send
            encoded_params = urllib.urlencode(params)
            return self.__remote_http_get("projects/%s/%s?%s" % (project_id, sub_url, encoded_params))
        else:
            # no arguments, get all iterations
            return self.__remote_http_get("projects/%s/%s" % (project_id, sub_url))

    def __perform_request(self, req):
        try:
            response = urllib2.urlopen(req)
            return json.loads(response.read())

        except urllib2.HTTPError, e:
            if e.code == 422:
                return json.loads(e.read())
            else:
                raise

    def __remote_http_get(self, path):

        url = self.__base_url + path
        req = urllib2.Request(url, None, {'X-TrackerToken': self.__token})
        return self.__perform_request(req)

    def __remote_http_post(self, path, data):

        data = json.dumps(data)

        url = self.__base_url + path
        req = urllib2.Request(url, data, {'X-TrackerToken': self.__token, 'Content-type': 'application/json'})
        return self.__perform_request(req)
    
    def __remote_http_put(self, path, data):

        data = json.dumps(data)

        url = self.__base_url + path
        req = urllib2.Request(url, data, {'X-TrackerToken': self.__token, 'Content-type': 'application/json'})
        req.get_method = lambda: 'PUT'
        return self.__perform_request(req)
    
    def __remote_http_delete(self, path):
        url = self.__base_url + path
        req = urllib2.Request(url, None, {'X-TrackerToken': self.__token})
        req.get_method = lambda: 'DELETE'
        return self.__perform_request(req)
